# P7-002: schedule only on Voragon GPU nodes (see node-type=gpu in main.tf).
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
        - matchExpressions:
            - key: node-type
              operator: In
              values:
                - gpu

tolerations:
  - key: nvidia.com/gpu
    operator: Exists
    effect: NoSchedule
