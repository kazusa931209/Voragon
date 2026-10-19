resource "aws_cloudwatch_log_group" "realtime_backend" {
  name              = var.cloudwatch_log_group_name
  retention_in_days = var.cloudwatch_log_retention_days
}

data "aws_iam_policy_document" "fluent_bit_logs" {
  statement {
    sid    = "CloudWatchLogsWrite"
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:DescribeLogStreams",
      "logs:PutLogEvents",
    ]
    resources = ["${aws_cloudwatch_log_group.realtime_backend.arn}:*"]
  }
}

resource "aws_iam_policy" "fluent_bit_logs" {
  name        = "${var.cluster_name}-fluent-bit-logs"
  description = "Fluent Bit write access to ${var.cloudwatch_log_group_name}"
  policy      = data.aws_iam_policy_document.fluent_bit_logs.json
}

module "fluent_bit_irsa" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.52"

  role_name = "${var.cluster_name}-fluent-bit"

  role_policy_arns = {
    cloudwatch_logs = aws_iam_policy.fluent_bit_logs.arn
  }

  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["amazon-cloudwatch:fluent-bit"]
    }
  }
}

resource "helm_release" "fluent_bit" {
  name             = "fluent-bit"
  repository       = "https://fluent.github.io/helm-charts"
  chart            = "fluent-bit"
  namespace        = "amazon-cloudwatch"
  create_namespace = true
  version          = "0.47.10"
  wait             = true
  timeout          = 600

  values = [
    templatefile("${path.module}/fluent_bit_values.yaml.tpl", {
      irsa_role_arn  = module.fluent_bit_irsa.iam_role_arn
      aws_region     = var.aws_region
      log_group_name = aws_cloudwatch_log_group.realtime_backend.name
    }),
  ]

  depends_on = [
    module.eks,
    aws_cloudwatch_log_group.realtime_backend,
    module.fluent_bit_irsa,
  ]
}
