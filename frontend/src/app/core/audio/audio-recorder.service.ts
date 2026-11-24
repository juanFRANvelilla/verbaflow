import { Injectable, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class AudioRecorderService {
  readonly recording = signal(false);

  private mediaRecorder: MediaRecorder | null = null;
  private chunks: BlobPart[] = [];

  async start(): Promise<void> {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    this.chunks = [];
    this.mediaRecorder = new MediaRecorder(stream, { mimeType: this.preferredMime() });
    this.mediaRecorder.ondataavailable = (ev) => {
      if (ev.data.size > 0) {
        this.chunks.push(ev.data);
      }
    };
    this.mediaRecorder.start();
    this.recording.set(true);
  }

  async stop(): Promise<Blob> {
    const recorder = this.mediaRecorder;
    if (!recorder) {
      throw new Error('No hay grabación activa');
    }
    return new Promise((resolve, reject) => {
      recorder.onstop = () => {
        this.recording.set(false);
        recorder.stream.getTracks().forEach((t) => t.stop());
        resolve(new Blob(this.chunks, { type: recorder.mimeType || 'audio/webm' }));
      };
      recorder.onerror = () => reject(new Error('Error de grabación'));
      recorder.stop();
    });
  }

  private preferredMime(): string {
    const candidates = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4'];
    return candidates.find((m) => MediaRecorder.isTypeSupported(m)) ?? '';
  }
}