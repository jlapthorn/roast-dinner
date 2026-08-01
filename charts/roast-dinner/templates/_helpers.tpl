{{/*
Expand the name of the chart.
*/}}
{{- define "roast-dinner.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "roast-dinner.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "roast-dinner.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "roast-dinner.labels" -}}
helm.sh/chart: {{ include "roast-dinner.chart" . }}
{{ include "roast-dinner.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "roast-dinner.selectorLabels" -}}
app.kubernetes.io/name: {{ include "roast-dinner.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Service account name
*/}}
{{- define "roast-dinner.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "roast-dinner.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
PVC name
*/}}
{{- define "roast-dinner.pvcName" -}}
{{- if .Values.persistence.existingClaim }}
{{- .Values.persistence.existingClaim }}
{{- else }}
{{- include "roast-dinner.fullname" . }}-data
{{- end }}
{{- end }}

{{/*
SECRET_KEY: use provided value, existing secret, or generate once.
*/}}
{{- define "roast-dinner.secretKey" -}}
{{- if .Values.secretKey }}
{{- .Values.secretKey }}
{{- else }}
{{- $secretName := printf "%s-app" (include "roast-dinner.fullname" .) }}
{{- $existing := lookup "v1" "Secret" .Release.Namespace $secretName }}
{{- if and $existing $existing.data (index $existing.data "SECRET_KEY") }}
{{- index $existing.data "SECRET_KEY" | b64dec }}
{{- else }}
{{- randAlphaNum 32 }}
{{- end }}
{{- end }}
{{- end }}
