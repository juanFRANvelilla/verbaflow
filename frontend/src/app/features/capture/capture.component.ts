import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { EmptyError, firstValueFrom, Observable, Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { LookupResponse, VerbaflowApiService } from '../../core/api/verbaflow-api.service';
import { BrowserSpeechService } from '../../core/audio/browser-speech.service';
import { LanguageSelectionService } from '../../core/language/language-selection.service';

@Component({
  selector: 'app-capture',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './capture.component.html',
  styleUrl: './capture.component.scss',
})
export class CaptureComponent {
  private readonly browserSpeech = inject(BrowserSpeechService);
  private readonly api = inject(VerbaflowApiService);
  private readonly languages = inject(LanguageSelectionService);

  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly result = signal<LookupResponse | null>(null);
  readonly editableText = signal('');

  private requestCancel: Subject<void> | null = null;

  get recording() {
    return this.browserSpeech.listening();
  }

  async startRecord(): Promise<void> {
    if (this.loading() || this.recording) {
      return;
    }
    this.error.set(null);
    try {
      await this.browserSpeech.start(this.languages.selectedCode());
    } catch (e: unknown) {
      this.error.set(e instanceof Error ? e.message : 'No se pudo acceder al micrófono');
    }
  }

  cancelRecord(): void {
    this.browserSpeech.cancel();
  }

  cancelBusy(): void {
    this.endCancellableRequest();
    this.browserSpeech.cancel();
    this.loading.set(false);
  }

  async finishRecord(): Promise<void> {
    if (!this.recording) {
      return;
    }
    this.loading.set(true);
    this.error.set(null);
    this.beginCancellableRequest();
    try {
      const speech = await this.browserSpeech.stop();
      if (!this.requestCancel) {
        return;
      }
      this.editableText.set(speech.bestText);
      const res = await this.awaitCancellable(
        this.api.lookupText(speech.bestText, this.languages.selectedCode(), 'browser'),
      );
      this.result.set(res);
    } catch (e: unknown) {
      if (!this.isCancelledError(e)) {
        this.error.set(this.formatError(e));
      }
    } finally {
      this.endCancellableRequest();
      this.loading.set(false);
    }
  }

  async refreshTranslation(): Promise<void> {
    const text = this.editableText().trim();
    if (!text) {
      return;
    }
    this.loading.set(true);
    this.error.set(null);
    this.beginCancellableRequest();
    try {
      const res = await this.awaitCancellable(
        this.api.lookupText(text, this.languages.selectedCode(), 'manual'),
      );
      this.result.set(res);
    } catch (e: unknown) {
      if (!this.isCancelledError(e)) {
        this.error.set(this.formatError(e));
      }
    } finally {
      this.endCancellableRequest();
      this.loading.set(false);
    }
  }

  discard(): void {
    this.result.set(null);
    this.editableText.set('');
    this.error.set(null);
  }

  async save(): Promise<void> {
    const r = this.result();
    const text = this.editableText().trim();
    if (!r || !text) {
      return;
    }
    this.loading.set(true);
    this.beginCancellableRequest();
    try {
      await this.awaitCancellable(
        this.api.saveEntry({
          language_code: r.language_code,
          text,
          translation: r.llm.translation_es,
          example_text: r.llm.example_en || null,
        }),
      );
      this.discard();
    } catch (e: unknown) {
      if (!this.isCancelledError(e)) {
        this.error.set(this.formatError(e));
      }
    } finally {
      this.endCancellableRequest();
      this.loading.set(false);
    }
  }

  private beginCancellableRequest(): void {
    this.endCancellableRequest();
    this.requestCancel = new Subject<void>();
  }

  private endCancellableRequest(): void {
    const cancel$ = this.requestCancel;
    if (!cancel$) {
      return;
    }
    cancel$.next();
    cancel$.complete();
    this.requestCancel = null;
  }

  private awaitCancellable<T>(source: Observable<T>): Promise<T> {
    const cancel$ = this.requestCancel;
    if (!cancel$) {
      return firstValueFrom(source);
    }
    return firstValueFrom(source.pipe(takeUntil(cancel$)));
  }

  private isCancelledError(e: unknown): boolean {
    if (e instanceof EmptyError) {
      return true;
    }
    if (e instanceof Error && (e.message === 'Cancelado' || e.name === 'AbortError')) {
      return true;
    }
    return typeof DOMException !== 'undefined' && e instanceof DOMException && e.name === 'AbortError';
  }

  private formatError(e: unknown): string {
    if (e instanceof HttpErrorResponse) {
      const detail = e.error?.detail;
      if (typeof detail === 'string' && detail.trim()) {
        return detail;
      }
      if (Array.isArray(detail) && detail.length) {
        return String(detail[0]?.msg ?? detail[0]);
      }
      return e.message || 'Error en la petición';
    }
    return e instanceof Error ? e.message : 'Error desconocido';
  }
}