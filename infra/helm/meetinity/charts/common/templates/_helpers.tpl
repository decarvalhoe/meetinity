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

{{/* Observability helpers */}}

{{- define "common.observabilityConfig" -}}
{{- $config := dict -}}
{{- with .Values.global }}
  {{- with .observability }}
    {{- $config = mergeOverwrite (deepCopy $config) (deepCopy .) -}}
  {{- end -}}
{{- end -}}
{{- with .Values.observability }}
  {{- $config = mergeOverwrite (deepCopy $config) (deepCopy .) -}}
{{- end -}}
{{- toYaml $config -}}
{{- end -}}

{{- define "common.tracingAgentContainers" -}}
{{- $tracing := .tracing | default (dict) -}}
{{- $serviceName := .serviceName -}}
{{- if and ($tracing.enabled | default false) (and $tracing.agent ($tracing.agent.enabled | default false)) }}
- name: {{ default "tracing-agent" $tracing.agent.name }}
  image: "{{ $tracing.agent.image.repository }}:{{ $tracing.agent.image.tag }}"
  imagePullPolicy: {{ default "IfNotPresent" $tracing.agent.image.pullPolicy }}
  {{- with $tracing.agent.securityContext }}
  securityContext:
    {{- toYaml . | nindent 4 }}
  {{- end }}
  {{- $collector := $tracing.agent.collector | default (dict) -}}
  {{- $args := $tracing.agent.extraArgs | default list -}}
  args:
    {{- if gt (len $args) 0 }}
      {{- range $args }}
    - {{ . | quote }}
      {{- end }}
    {{- else }}
    - "--reporter.grpc.host-port={{ printf "%s:%v" (default "jaeger-collector.observability.svc.cluster.local" $collector.host) (default 14250 $collector.port) }}"
    - "--agent.tags=service.name={{ $serviceName }}"
    {{- end }}
  env:
    - name: POD_IP
      valueFrom:
        fieldRef:
          fieldPath: status.podIP
    {{- with $collector.host }}
    - name: JAEGER_COLLECTOR_HOST
      value: {{ . | quote }}
    {{- end }}
    {{- with $collector.port }}
    - name: JAEGER_COLLECTOR_PORT
      value: "{{ . }}"
    {{- end }}
    {{- range $env := ($tracing.agent.env | default list) }}
    - name: {{ $env.name }}
      {{- if $env.valueFrom }}
      valueFrom:
        {{- toYaml $env.valueFrom | nindent 8 }}
      {{- else }}
      value: {{ $env.value | quote }}
      {{- end }}
    {{- end }}
  {{- if $tracing.agent.ports }}
  ports:
    {{- toYaml $tracing.agent.ports | nindent 4 }}
  {{- end }}
  {{- if $tracing.agent.resources }}
  resources:
    {{- toYaml $tracing.agent.resources | nindent 4 }}
  {{- end }}
  {{- if $tracing.agent.extraVolumeMounts }}
  volumeMounts:
    {{- toYaml $tracing.agent.extraVolumeMounts | nindent 4 }}
  {{- end }}
  {{- if $tracing.agent.livenessProbe }}
  livenessProbe:
    {{- toYaml $tracing.agent.livenessProbe | nindent 4 }}
  {{- end }}
  {{- if $tracing.agent.readinessProbe }}
  readinessProbe:
    {{- toYaml $tracing.agent.readinessProbe | nindent 4 }}
  {{- end }}
{{- end }}
{{- end -}}

{{- define "common.tracingAgentVolumes" -}}
{{- $tracing := .tracing | default (dict) -}}
{{- if and ($tracing.enabled | default false) (and $tracing.agent ($tracing.agent.enabled | default false)) ($tracing.agent.extraVolumes) }}
{{- toYaml $tracing.agent.extraVolumes -}}
{{- end -}}
{{- end -}}
{{- end }}
