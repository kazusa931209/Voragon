resource "helm_release" "nvidia_device_plugin" {
  count = var.enable_gpu_node_group ? 1 : 0

  name       = "nvidia-device-plugin"
  repository = "https://nvidia.github.io/k8s-device-plugin"
  chart      = "nvidia-device-plugin"
  version    = var.nvidia_device_plugin_chart_version
  namespace  = "kube-system"
  wait       = true
  timeout    = 600

  values = [file("${path.module}/nvidia_device_plugin_values.yaml.tpl")]

  depends_on = [module.eks]
}
