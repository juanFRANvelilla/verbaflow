import { Component, inject, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { LanguageSelectionService } from './core/language/language-selection.service';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, RouterLinkActive, FormsModule],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App implements OnInit {
  private readonly languages = inject(LanguageSelectionService);

  readonly languageList = this.languages.languages;
  readonly selectedLanguage = this.languages.selectedCode;

  ngOnInit(): void {
    this.languages.loadLanguages();
  }

  onLanguageChange(code: string): void {
    this.languages.setSelected(code);
  }
}