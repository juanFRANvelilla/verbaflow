import { Component } from '@angular/core';

@Component({
  selector: 'app-review',
  standalone: true,
  template: `
    <main class="vf-page">
      <div class="vf-card review-soon">
        <p class="vf-label">Próximamente</p>
        <h2 class="review-title">Repaso espaciado</h2>
        <p class="vf-hint">
          Aquí entrará FSRS para repasar lo guardado en biblioteca. De momento usa Grabar y Biblioteca.
        </p>
      </div>
    </main>
  `,
  styles: [
    `
      .review-soon {
        text-align: center;
        padding: 2.5rem 1.5rem;
      }
      .review-title {
        margin: 0.5rem 0 1rem;
        font-size: 1.35rem;
        font-weight: 700;
        color: #fff;
      }
    `,
  ],
})
export class ReviewPlaceholderComponent {}