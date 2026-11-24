import { Injectable, signal } from '@angular/core';

export type SpeechListenResult = {
  bestText: string;
  alternatives: string[];
};

type SpeechRecognitionLike = {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  maxAlternatives: number;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onresult: ((ev: { results: { length: number; [index: number]: { isFinal?: boolean; [i: number]: { transcript?: string } } } }) => void) | null;
  onerror: ((ev: { error: string }) => void) | null;
  onend: (() => void) | null;
};

declare global {
  interface Window {
    SpeechRecognition?: new () => SpeechRecognitionLike;
    webkitSpeechRecognition?: new () => SpeechRecognitionLike;
  }
}

@Injectable({ providedIn: 'root' })
export class BrowserSpeechService {
  readonly listening = signal(false);

  private recognition: SpeechRecognitionLike | null = null;
  private pending: {
    resolve: (r: SpeechListenResult) => void;
    reject: (e: Error) => void;
  } | null = null;
  private settled = false;
  private currentTranscript = '';
  private stopWaitTimer: ReturnType<typeof setTimeout> | null = null;

  private static readonly STOP_WAIT_MS = 12_000;

  isSupported(): boolean {
    return typeof window !== 'undefined' && !!(window.SpeechRecognition || window.webkitSpeechRecognition);
  }

  langForCode(code: string): string {
    const map: Record<string, string> = {
      en: 'en-US',
      es: 'es-ES',
    };
    return map[code] ?? 'en-US';
  }

  start(languageCode: string): void {
    if (!this.isSupported()) {
      throw new Error('Tu navegador no soporta reconocimiento de voz.');
    }
    this.recognition?.abort();
    this.settled = false;
    this.pending = null;
    this.currentTranscript = '';

    const Recognition = window.SpeechRecognition ?? window.webkitSpeechRecognition!;
    const recognition = new Recognition();
    this.recognition = recognition;
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.maxAlternatives = 3;
    recognition.lang = this.langForCode(languageCode);

    recognition.onresult = (event) => {
      let transcript = '';
      for (let i = 0; i < event.results.length; i++) {
        transcript += event.results[i][0]?.transcript ?? '';
      }
      this.currentTranscript = transcript.trim();
    };

    recognition.onerror = (event) => {
      if (this.settled) {
        return;
      }
      this.settled = true;
      this.clearStopWaitTimer();
      this.listening.set(false);
      const msg =
        event.error === 'not-allowed'
          ? 'Permiso de micrófono o Dictado denegado (Safari: Ajustes > Teclado > Dictado)'
          : event.error === 'no-speech'
            ? 'No se detectó voz'
            : `Error de voz: ${event.error}`;
      this.pending?.reject(new Error(msg));
      this.pending = null;
    };

    recognition.onend = () => {
      this.clearStopWaitTimer();
      this.listening.set(false);
      if (this.settled || !this.pending) {
        return;
      }
      this.settled = true;
      if (this.currentTranscript) {
        this.pending.resolve({ bestText: this.currentTranscript, alternatives: [] });
      } else {
        this.pending.reject(
          new Error('No se detectó voz. En Safari activa Dictado y habla antes de pulsar Parar.'),
        );
      }
      this.pending = null;
    };

    this.listening.set(true);
    recognition.start();
  }

  stop(): Promise<SpeechListenResult> {
    const recognition = this.recognition;
    if (!recognition) {
      return Promise.reject(new Error('No hay escucha activa'));
    }
    return new Promise((resolve, reject) => {
      this.pending = { resolve, reject };
      this.stopWaitTimer = setTimeout(() => {
        if (this.settled) {
          return;
        }
        this.settled = true;
        const text = this.currentTranscript;
        this.recognition?.abort();
        this.listening.set(false);
        if (text) {
          resolve({ bestText: text, alternatives: [] });
        } else {
          reject(new Error('No se pudo obtener el audio a tiempo. Prueba de nuevo o escribe la palabra.'));
        }
        this.pending = null;
        this.stopWaitTimer = null;
      }, BrowserSpeechService.STOP_WAIT_MS);
      recognition.stop();
    });
  }

  cancel(): void {
    this.clearStopWaitTimer();
    if (!this.settled && this.pending) {
      this.settled = true;
      this.pending.reject(new Error('Cancelado'));
      this.pending = null;
    } else {
      this.settled = true;
    }
    this.currentTranscript = '';
    this.recognition?.abort();
    this.recognition = null;
    this.listening.set(false);
  }

  private clearStopWaitTimer(): void {
    if (this.stopWaitTimer !== null) {
      clearTimeout(this.stopWaitTimer);
      this.stopWaitTimer = null;
    }
  }
}