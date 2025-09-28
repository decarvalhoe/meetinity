{{- define "meetinity.name" -}}
{{- .Chart.Name -}}
{{- end }}

{{- define "meetinity.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "meetinity.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end }}

{{- define "meetinity.labels" -}}
app.kubernetes.io/name: {{ include "meetinity.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: meetinity
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
{{- end }}
