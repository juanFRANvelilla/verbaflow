#!/usr/bin/env bash
# Ejecutar en un host con kubectl (p. ej. 192.168.0.176).
set -euo pipefail

NS=verbaflow
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

kubectl get namespace "$NS" >/dev/null 2>&1 || kubectl create namespace "$NS"

kubectl apply -f "${SCRIPT_DIR}/jenkins-rolebinding.yaml"

if ! kubectl get secret ghcr-secret -n "$NS" >/dev/null 2>&1; then
  copied=false
  for candidate in surplus-satellite pre-finance-portfolio-back pre-finance-portfolio-front; do
    if kubectl get secret ghcr-secret -n "$candidate" >/dev/null 2>&1; then
      echo "Copiando ghcr-secret desde ${candidate}..."
      kubectl get secret ghcr-secret -n "$candidate" -o yaml \
        | sed "s/namespace: ${candidate}/namespace: ${NS}/" \
        | grep -vE '^\s*(resourceVersion|uid|creationTimestamp):' \
        | kubectl apply -f -
      copied=true
      break
    fi
  done
  if [ "$copied" = false ] && kubectl get secret regcred -n jenkins >/dev/null 2>&1; then
    echo "Copiando regcred (jenkins) como ghcr-secret..."
    kubectl get secret regcred -n jenkins -o yaml \
      | sed "s/namespace: jenkins/namespace: ${NS}/" \
      | sed 's/name: regcred/name: ghcr-secret/' \
      | grep -vE '^\s*(resourceVersion|uid|creationTimestamp):' \
      | kubectl apply -f -
    copied=true
  fi
  if [ "$copied" = false ]; then
    echo "No encontré ghcr-secret ni regcred para copiar."
    exit 1
  fi
else
  echo "ghcr-secret ya existe en ${NS}"
fi

if kubectl get secret backend-secrets -n "$NS" >/dev/null 2>&1; then
  echo "backend-secrets ya existe en ${NS}; no se sobrescribe."
  exit 0
fi

SOURCE_NS=""
SOURCE_NAME="backend-secrets"

if kubectl get secret backend-secrets -n pre-finance-portfolio-back >/dev/null 2>&1; then
  SOURCE_NS=pre-finance-portfolio-back
elif kubectl get secret backend-secrets -n surplus-satellite >/dev/null 2>&1; then
  SOURCE_NS=surplus-satellite
elif kubectl get secret surplus-satellite-secrets -n surplus-satellite >/dev/null 2>&1; then
  SOURCE_NS=surplus-satellite
  SOURCE_NAME=surplus-satellite-secrets
fi

if [ -z "$SOURCE_NS" ]; then
  echo "No encontré backend-secrets en finance/satellite. Crea backend-secrets en ${NS} a mano."
  exit 1
fi

echo "Creando backend-secrets en ${NS} desde ${SOURCE_NS}/${SOURCE_NAME}..."

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

kubectl get secret "$SOURCE_NAME" -n "$SOURCE_NS" -o go-template='{{range $k,$v := .data}}{{$k}}{{"\n"}}{{end}}' \
  >"$tmpdir/keys"

args=()
while IFS= read -r key; do
  [ -z "$key" ] && continue
  val="$(kubectl get secret "$SOURCE_NAME" -n "$SOURCE_NS" -o "jsonpath={.data.${key}}" | base64 -d)"
  if [ "$key" = "DATABASE_URL" ]; then
  val="$(echo "$val" | sed -E 's#^(postgresql(\+asyncpg)?://[^/]+)/[^?]+#\1/verbaflow#')"
    case "$val" in
      postgresql://*) val="postgresql+asyncpg://${val#postgresql://}" ;;
    esac
  fi
  args+=(--from-literal="${key}=${val}")
done <"$tmpdir/keys"

kubectl create secret generic backend-secrets -n "$NS" "${args[@]}"
echo "Listo: ghcr-secret, backend-secrets y RoleBinding en ${NS}"
kubectl get secrets -n "$NS" | grep -E 'NAME|ghcr|backend'