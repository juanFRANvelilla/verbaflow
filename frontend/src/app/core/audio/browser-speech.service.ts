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
  onstart: (() => void) | null;
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
  private iosMode = false;
  private restartTimer: ReturnType<typeof setTimeout> | null = null;
  private bootstrapping = false;

  private static readonly STOP_WAIT_MS = 12_000;

  isSupported(): boolean {
    return typeof window !== 'undefined' && !!(window.SpeechRecognition || window.webkitSpeechRecognition);
  }

  isIosDevice(): boolean {
    if (typeof navigator === 'undefined') {
      return false;
    }
    const ua = navigator.userAgent;
    const iOS = /iPad|iPhone|iPod/.test(ua);
    const iPadOs =
      navigator.platform === 'MacIntel' && typeof navigator.maxTouchPoints === 'number' && navigator.maxTouchPoints > 1;
    return iOS || iPadOs;
  }

  langForCode(code: string): string {
    const map: Record<string, string> = {
      en: 'en-US',
      es: 'es-ES',
    };
    return map[code] ?? 'en-US';
  }

  async start(languageCode: string): Promise<void> {
    if (!this.isSupported()) {
      throw new Error('Tu navegador no soporta reconocimiento de voz.');
    }
    if (this.listening() || this.bootstrapping) {
      return;
    }
    this.bootstrapping = true;

    if (this.isIosDevice() && typeof navigator.mediaDevices?.getUserMedia === 'function') {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        for (const track of stream.getTracks()) {
          track.stop();
        }
      } catch {
        this.bootstrapping = false;
        throw new Error(
          'Permiso de micrófono denegado. En iPhone: Ajustes > Safari > Micrófono (o la web de Verbaflow) y vuelve a intentarlo.',
        );
      }
    }

    this.cancel();
    this.settled = false;
    this.pending = null;
    this.currentTranscript = '';
    this.iosMode = this.isIosDevice();

    const Recognition = window.SpeechRecognition ?? window.webkitSpeechRecognition!;
    const recognition = new Recognition();
    this.recognition = recognition;
    recognition.continuous = this.iosMode;
    recognition.interimResults = true;
    recognition.maxAlternatives = this.iosMode ? 1 : 3;
    recognition.lang = this.langForCode(languageCode);

    return new Promise<void>((resolve, reject) => {
      let started = false;

      const endBootstrap = () => {
        this.bootstrapping = false;
      };

      const failStart = (msg: string) => {
        if (this.settled) {
          endBootstrap();
          return;
        }
        this.settled = true;
        this.clearStopWaitTimer();
        this.clearRestartTimer();
        this.listening.set(false);
        this.recognition?.abort();
        endBootstrap();
        if (this.pending) {
          this.pending.reject(new Error(msg));
          this.pending = null;
        } else if (!started) {
          reject(new Error(msg));
        }
      };

      recognition.onresult = (event) => {
        let transcript = '';
        for (let i = 0; i < event.results.length; i++) {
          transcript += event.results[i][0]?.transcript ?? '';
        }
        this.currentTranscript = transcript.trim();
      };

      recognition.onstart = () => {
        started = true;
        this.listening.set(true);
        endBootstrap();
        resolve();
      };

      recognition.onerror = (event) => {
        if (this.settled || event.error === 'aborted') {
          return;
        }
        if (this.iosMode && (event.error === 'no-speech' || event.error === 'no-match') && !this.pending) {
          return;
        }
        failStart(this.errorMessage(event.error));
      };

      recognition.onend = () => {
        this.clearStopWaitTimer();
        if (this.settled) {
          this.listening.set(false);
          return;
        }

        if (!this.pending) {
          if (this.iosMode && this.recognition) {
            this.scheduleIosRestart();
            return;
          }
          this.listening.set(false);
          return;
        }

        this.settled = true;
        this.listening.set(false);
        if (this.currentTranscript) {
          this.pending.resolve({ bestText: this.currentTranscript, alternatives: [] });
        } else {
          this.pending.reject(
            new Error(
              this.iosMode
                ? 'No se detectó voz. Pulsa Parar después de hablar la palabra.'
                : 'No se detectó voz. Habla antes de pulsar Parar.',
            ),
          );
        }
        this.pending = null;
      };

      try {
        recognition.start();
      } catch (e: unknown) {
        failStart(e instanceof Error ? e.message : 'No se pudo iniciar el micrófono');
      }
    });
  }

  stop(): Promise<SpeechListenResult> {
    const recognition = this.recognition;
    if (!recognition) {
      return Promise.reject(new Error('No hay escucha activa'));
    }
    this.clearRestartTimer();
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
      try {
        recognition.stop();
      } catch {
        recognition.abort();
      }
    });
  }

  cancel(): void {
    this.clearStopWaitTimer();
    this.clearRestartTimer();
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
    this.bootstrapping = false;
  }

  private scheduleIosRestart(): void {
    this.clearRestartTimer();
    this.restartTimer = setTimeout(() => {
      if (this.settled || this.pending || !this.recognition) {
        return;
      }
      try {
        this.recognition.start();
      } catch {
        this.clearRestartTimer();
        this.restartTimer = setTimeout(() => this.scheduleIosRestart(), 120);
      }
    }, 80);
  }

  private clearRestartTimer(): void {
    if (this.restartTimer !== null) {
      clearTimeout(this.restartTimer);
      this.restartTimer = null;
    }
  }

  private clearStopWaitTimer(): void {
    if (this.stopWaitTimer !== null) {
      clearTimeout(this.stopWaitTimer);
      this.stopWaitTimer = null;
    }
  }

  private errorMessage(code: string): string {
    if (code === 'not-allowed') {
      return this.isIosDevice()
        ? 'Micrófono o reconocimiento de voz no permitido. Revisa Ajustes > Safari y el permiso de micrófono para esta web.'
        : 'Permiso de micrófono denegado';
    }
    if (code === 'no-speech') {
      return 'No se detectó voz';
    }
    if (code === 'service-not-allowed') {
      return 'Reconocimiento de voz no disponible (en iPhone usa Safari, no el navegador dentro de otra app).';
    }
    return `Error de voz: ${code}`;
  }
}