{{- define "search-service.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "search-service.releaseName" -}}
{{- include "common.releaseName" (dict "context" . "name" (include "search-service.name" .)) -}}
{{- end -}}

{{- define "search-service.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- include "search-service.releaseName" . -}}
{{- end -}}
{{- end -}}

{{- define "search-service.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
app.kubernetes.io/name: {{ include "search-service.name" . }}
app.kubernetes.io/instance: {{ include "search-service.releaseName" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{- define "search-service.selectorLabels" -}}
app.kubernetes.io/name: {{ include "search-service.name" . }}
app.kubernetes.io/instance: {{ include "search-service.releaseName" . }}
{{- end -}}

{{- define "search-service.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- if .Values.serviceAccount.name -}}
{{- .Values.serviceAccount.name -}}
{{- else -}}
{{- include "search-service.fullname" . -}}
{{- end -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}
