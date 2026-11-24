import { Component, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { LookupResponse, VerbaflowApiService } from '../../core/api/verbaflow-api.service';
import { AudioRecorderService } from '../../core/audio/audio-recorder.service';

@Component({
  selector: 'app-capture',
  standalone: true,
  templateUrl: './capture.component.html',
  styleUrl: './capture.component.scss',
})
export class CaptureComponent {
  private readonly recorder = inject(AudioRecorderService);
  private readonly api = inject(VerbaflowApiService);

  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly result = signal<LookupResponse | null>(null);

  get recording() {
    return this.recorder.recording();
  }

  async toggleRecord(): Promise<void> {
    this.error.set(null);
    if (this.recorder.recording()) {
      this.loading.set(true);
      try {
        const blob = await this.recorder.stop();
        const res = await firstValueFrom(this.api.lookup(blob));
        this.result.set(res);
      } catch (e: unknown) {
        this.error.set(e instanceof Error ? e.message : 'Error en lookup');
      } finally {
        this.loading.set(false);
      }
      return;
    }
    try {
      await this.recorder.start();
    } catch {
      this.error.set('No se pudo acceder al micrófono (¿HTTPS?)');
    }
  }

  async save(): Promise<void> {
    const r = this.result();
    if (!r) {
      return;
    }
    this.loading.set(true);
    try {
      await firstValueFrom(this.api.saveLookup(r.lookup_id));
      this.error.set(null);
    } catch (e: unknown) {
      this.error.set(e instanceof Error ? e.message : 'No se pudo guardar');
    } finally {
      this.loading.set(false);
    }
  }
}