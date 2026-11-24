-- Verbaflow — creación de rol, base de datos y esquema inicial
-- Ejecutar conectado como superusuario (postgres) salvo el bloque final.

-- 1) Rol y base de datos (ajusta la contraseña en producción)
CREATE ROLE verbaflow WITH LOGIN PASSWORD 'CAMBIA_ESTA_PASSWORD';
CREATE DATABASE verbaflow OWNER verbaflow ENCODING 'UTF8' TEMPLATE template0;

-- A partir de aquí, conectar a la BD verbaflow:
--   \c verbaflow

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2) Tipos enumerados
CREATE TYPE source_kind AS ENUM ('series', 'book', 'other');
CREATE TYPE vocab_kind AS ENUM ('word', 'phrase', 'phrasal_verb', 'idiom', 'other');

-- 3) Tablas
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(320) UNIQUE,
    display_name VARCHAR(120),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE sources (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users (id),
    kind source_kind NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_sources_user_id ON sources (user_id);

CREATE TABLE vocab_items (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users (id),
    canonical_en TEXT NOT NULL,
    kind vocab_kind NOT NULL,
    translation_es TEXT NOT NULL,
    example_en TEXT,
    example_es TEXT,
    notes TEXT,
    phonetic_hint TEXT,
    metadata JSONB,
    source_id UUID REFERENCES sources (id),
    from_lookup_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_vocab_user_canonical UNIQUE (user_id, canonical_en)
);
CREATE INDEX ix_vocab_items_user_id ON vocab_items (user_id);

CREATE TABLE lookup_events (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users (id),
    audio_duration_ms INTEGER,
    stt_model VARCHAR(64),
    llm_model VARCHAR(128),
    stt_best_text TEXT,
    stt_raw_json JSONB,
    llm_response_json JSONB,
    selected_text TEXT,
    saved_vocab_id UUID REFERENCES vocab_items (id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_lookup_events_user_id ON lookup_events (user_id);

CREATE TABLE vocab_tags (
    vocab_id UUID NOT NULL REFERENCES vocab_items (id),
    tag VARCHAR(64) NOT NULL,
    PRIMARY KEY (vocab_id, tag),
    CONSTRAINT uq_vocab_tag UNIQUE (vocab_id, tag)
);

CREATE TABLE review_cards (
    id UUID PRIMARY KEY,
    vocab_id UUID NOT NULL UNIQUE REFERENCES vocab_items (id),
    user_id UUID NOT NULL REFERENCES users (id),
    stability DOUBLE PRECISION NOT NULL,
    difficulty DOUBLE PRECISION NOT NULL,
    due TIMESTAMPTZ NOT NULL,
    reps INTEGER NOT NULL,
    lapses INTEGER NOT NULL,
    last_review TIMESTAMPTZ,
    state SMALLINT NOT NULL,
    suspended BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_review_cards_user_id ON review_cards (user_id);
CREATE INDEX ix_review_cards_due ON review_cards (user_id, due);

CREATE TABLE review_logs (
    id UUID PRIMARY KEY,
    card_id UUID NOT NULL REFERENCES review_cards (id),
    rating SMALLINT NOT NULL,
    reviewed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    scheduled_due_before TIMESTAMPTZ,
    scheduled_due_after TIMESTAMPTZ
);
CREATE INDEX ix_review_logs_card_id ON review_logs (card_id);

-- 4) Usuario por defecto (coincide con DEFAULT_USER_ID en api/.env)
INSERT INTO users (id, display_name)
VALUES ('00000000-0000-4000-8000-000000000001', 'default')
ON CONFLICT (id) DO NOTHING;

-- 5) Permisos del rol (si creaste tablas como postgres)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO verbaflow;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO verbaflow;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO verbaflow;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO verbaflow;