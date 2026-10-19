serviceAccount:
  create: true
  name: fluent-bit
  annotations:
    eks.amazonaws.com/role-arn: ${irsa_role_arn}

kind: DaemonSet

resources:
  requests:
    cpu: 50m
    memory: 64Mi
  limits:
    memory: 256Mi

config:
  service: |
    [SERVICE]
        Flush         1
        Log_Level     info
        Daemon        off
        Parsers_File  /fluent-bit/etc/parsers.conf
  inputs: |
    [INPUT]
        Name              tail
        Tag               kube.*
        Path              /var/log/containers/*.log
        Parser            cri
        DB                /var/log/flb_kube.db
        Mem_Buf_Limit     5MB
        Skip_Long_Lines   On
  filters: |
    [FILTER]
        Name                kubernetes
        Match               kube.*
        Kube_URL            https://kubernetes.default.svc:443
        Kube_CA_File        /var/log/secrets/kubernetes.io/serviceaccount/ca.crt
        Kube_Token_File     /var/log/secrets/kubernetes.io/serviceaccount/token
        Kube_Tag_Prefix     kube.var.log.containers.
        Merge_Log           On
        Keep_Log            Off
    [FILTER]
        Name    grep
        Match   kube.*
        Regex   $kubernetes['namespace_name'] voragon
    [FILTER]
        Name    grep
        Match   kube.*
        Regex   $kubernetes['labels']['app'] realtime-backend
  outputs: |
    [OUTPUT]
        Name                cloudwatch_logs
        Match               kube.*
        region              ${aws_region}
        log_group_name      ${log_group_name}
        log_stream_prefix   pod-
        auto_create_group   false
