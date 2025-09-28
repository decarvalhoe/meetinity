{{- define "meetinity.name" -}}
{{- .Chart.Name -}}
{{- end }}

{{- define "meetinity.releaseName" -}}
{{- include "common.releaseName" (dict "context" . "name" (include "meetinity.name" .)) -}}
{{- end }}

{{- define "meetinity.fullname" -}}
{{- include "meetinity.releaseName" . -}}
{{- end }}

{{- define "meetinity.labels" -}}
app.kubernetes.io/name: {{ include "meetinity.name" . }}
app.kubernetes.io/instance: {{ include "meetinity.releaseName" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: meetinity
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
{{- end }}
