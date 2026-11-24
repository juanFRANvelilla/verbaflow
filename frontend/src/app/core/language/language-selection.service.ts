import { Injectable, inject, signal } from '@angular/core';
import { Language, VerbaflowApiService } from '../api/verbaflow-api.service';

const STORAGE_KEY = 'verbaflow.selected_language';

const FALLBACK_LANGUAGES: Language[] = [{ code: 'en', name: 'English', enabled: true }];

function readStoredLanguageCode(): string {
  try {
    return localStorage.getItem(STORAGE_KEY) ?? 'en';
  } catch {
    return 'en';
  }
}

@Injectable({ providedIn: 'root' })
export class LanguageSelectionService {
  private readonly api = inject(VerbaflowApiService);

  readonly languages = signal<Language[]>(FALLBACK_LANGUAGES);
  readonly selectedCode = signal(readStoredLanguageCode());

  loadLanguages(): void {
    this.api.listLanguages().subscribe({
      next: (rows) => {
        this.languages.set(rows.length ? rows : FALLBACK_LANGUAGES);
        this.ensureSelectionValid();
      },
      error: () => {
        this.languages.set(FALLBACK_LANGUAGES);
        this.ensureSelectionValid();
      },
    });
  }

  setSelected(code: string): void {
    this.selectedCode.set(code);
    try {
      localStorage.setItem(STORAGE_KEY, code);
    } catch {
      /* almacenamiento no disponible */
    }
  }

  private ensureSelectionValid(): void {
    const rows = this.languages();
    if (!rows.length) {
      return;
    }
    if (!rows.some((l) => l.code === this.selectedCode())) {
      this.setSelected(rows[0].code);
    }
  }
}