{{- define "common.probeFields" -}}
{{- with .initialDelaySeconds }}
initialDelaySeconds: {{ . }}
{{- end }}
{{- with .periodSeconds }}
periodSeconds: {{ . }}
{{- end }}
{{- with .timeoutSeconds }}
timeoutSeconds: {{ . }}
{{- end }}
{{- with .successThreshold }}
successThreshold: {{ . }}
{{- end }}
{{- with .failureThreshold }}
failureThreshold: {{ . }}
{{- end }}
{{- end }}

{{- define "common.httpProbes" -}}
{{- $port := .port -}}
{{- with .liveness }}
livenessProbe:
  httpGet:
    path: {{ .path }}
    port: {{ default $port .port }}
    {{- with .scheme }}
    scheme: {{ . }}
    {{- end }}
  {{- include "common.probeFields" . | nindent 2 }}
{{- end }}
{{- with .readiness }}
readinessProbe:
  httpGet:
    path: {{ .path }}
    port: {{ default $port .port }}
    {{- with .scheme }}
    scheme: {{ . }}
    {{- end }}
  {{- include "common.probeFields" . | nindent 2 }}
{{- end }}
{{- end }}

{{- define "common.configmap" -}}
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ .name }}
  {{- if .labels }}
  labels:
    {{- toYaml .labels | nindent 4 }}
  {{- end }}
  {{- if .annotations }}
  annotations:
    {{- toYaml .annotations | nindent 4 }}
  {{- end }}
{{- if .binaryData }}
binaryData:
  {{- range $key, $value := .binaryData }}
  {{ $key }}: {{ $value | quote }}
  {{- end }}
{{- end }}
{{- if .data }}
data:
  {{- range $key, $value := .data }}
  {{ $key }}: {{ $value | quote }}
  {{- end }}
{{- end }}
{{- end }}

{{- define "common.sealedSecret" -}}
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: {{ .name }}
  {{- if .namespace }}
  namespace: {{ .namespace }}
  {{- end }}
  {{- if .labels }}
  labels:
    {{- toYaml .labels | nindent 4 }}
  {{- end }}
  {{- if .annotations }}
  annotations:
    {{- toYaml .annotations | nindent 4 }}
  {{- end }}
spec:
  encryptedData:
    {{- toYaml .encryptedData | nindent 4 }}
  template:
    metadata:
      {{- if .labels }}
      labels:
        {{- toYaml .labels | nindent 8 }}
      {{- end }}
      {{- if .annotations }}
      annotations:
        {{- toYaml .annotations | nindent 8 }}
      {{- end }}
    type: {{ default "Opaque" .type }}
{{- end }}

{{- define "common.externalSecret" -}}
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: {{ .name }}
  {{- if .namespace }}
  namespace: {{ .namespace }}
  {{- end }}
  {{- if .labels }}
  labels:
    {{- toYaml .labels | nindent 4 }}
  {{- end }}
  {{- if .annotations }}
  annotations:
    {{- toYaml .annotations | nindent 4 }}
  {{- end }}
spec:
  refreshInterval: {{ default "1h" .refreshInterval }}
  secretStoreRef:
    name: {{ .secretStoreRef.name }}
    kind: {{ default "ClusterSecretStore" .secretStoreRef.kind }}
  target:
    name: {{ default .name .target.name }}
    creationPolicy: {{ default "Owner" .target.creationPolicy }}
    {{- if .target.template }}
    template:
      {{- with .target.template.type }}
      type: {{ . }}
      {{- end }}
      {{- with .target.template.engineVersion }}
      engineVersion: {{ . }}
      {{- end }}
      {{- with .target.template.data }}
      data:
        {{- range $key, $value := . }}
        {{ $key }}: {{ $value | quote }}
        {{- end }}
      {{- end }}
    {{- end }}
  {{- if .data }}
  data:
    {{- range .data }}
    - secretKey: {{ .secretKey }}
      remoteRef:
        key: {{ .remoteRef.key }}
        {{- with .remoteRef.property }}
        property: {{ . }}
        {{- end }}
    {{- end }}
  {{- end }}
  {{- if .dataFrom }}
  dataFrom:
    {{- toYaml .dataFrom | nindent 4 }}
  {{- else }}
  dataFrom:
    - extract:
        key: {{ .path }}
{{- end }}

{{- define "common.environment" -}}
{{- $env := "" -}}
{{- with .Values.environment -}}
  {{- $env = . -}}
{{- end -}}
{{- if not $env -}}
  {{- with .Values.global -}}
    {{- with .environment -}}
      {{- $env = . -}}
    {{- end -}}
  {{- end -}}
{{- end -}}
{{- if not $env -}}
  {{- $env = .Release.Namespace -}}
{{- end -}}
{{- if not $env -}}
  {{- fail "environment value is required (set values.environment or global.environment)" -}}
{{- end -}}
{{- $sanitized := regexReplaceAll "[^a-z0-9-]" (lower $env) "-" -}}
{{- $sanitized = trimSuffix "-" $sanitized -}}
{{- if not $sanitized -}}
  {{- fail (printf "environment value '%s' resolves to an empty identifier" $env) -}}
{{- end -}}
{{- $sanitized -}}
{{- end -}}

{{- define "common.releaseName" -}}
{{- $ctx := .context | default . -}}
{{- $name := .name -}}
{{- if not $name -}}
  {{- fail "name is required for common.releaseName" -}}
{{- end -}}
{{- $env := include "common.environment" $ctx -}}
{{- printf "%s-%s" $name $env | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end }}
