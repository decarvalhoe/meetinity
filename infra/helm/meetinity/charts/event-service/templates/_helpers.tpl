{{- define "event-service.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "event-service.releaseName" -}}
{{- include "common.releaseName" (dict "context" . "name" (include "event-service.name" .)) -}}
{{- end -}}

{{- define "event-service.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- include "event-service.releaseName" . -}}
{{- end -}}
{{- end -}}

{{- define "event-service.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
app.kubernetes.io/name: {{ include "event-service.name" . }}
app.kubernetes.io/instance: {{ include "event-service.releaseName" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{- define "event-service.selectorLabels" -}}
app.kubernetes.io/name: {{ include "event-service.name" . }}
app.kubernetes.io/instance: {{ include "event-service.releaseName" . }}
{{- end -}}

{{- define "event-service.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- if .Values.serviceAccount.name -}}
{{- .Values.serviceAccount.name -}}
{{- else -}}
{{- include "event-service.fullname" . -}}
{{- end -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}
