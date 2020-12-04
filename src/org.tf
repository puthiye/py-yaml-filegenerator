resource "aws_organizations_organization" "organisation" {
  aws_service_access_principals = [
    "cloudtrail.amazonaws.com",
    "config.amazonaws.com",
    "ram.amazonaws.com",
    "sso.amazonaws.com",
    "tagpolicies.tag.amazonaws.com",
    "guardduty.amazonaws.com"
  ]
  feature_set = "ALL"
  enabled_policy_types = [
    "SERVICE_CONTROL_POLICY",
    "TAG_POLICY"
  ]
}

resource "aws_ssm_parameter" "organisation_id" {
  name  = "organisation-id"
  type  = "String"
  value = aws_organizations_organization.organisation.id
}

data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "assume_role_from_master" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }
  }
}

resource "aws_iam_role" "organization_account_access_role" {
  name               = "OrganizationAccountAccessRole"
  assume_role_policy = data.aws_iam_policy_document.assume_role_from_master.json
}


resource "aws_iam_role_policy_attachment" "organization_account_access_role" {
  role       = aws_iam_role.organization_account_access_role.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}

resource "aws_organizations_organizational_unit" "ou1" {
  name      = "${local.account_prefix}-ou-ou1"
  parent_id = aws_organizations_organization.organisation.roots[0].id
}


#OU_INSERT_BY_BAYAMI


# Organisation Unit SSM Parameter Store (used for lookup for account creation)
resource "aws_ssm_parameter" "organisational_units" {
  name = "organisational-units"
  type = "String"
  value = jsonencode({
    "root" : {
      "arn" : aws_organizations_organization.organisation.roots[0].arn,
      "id" :  aws_organizations_organization.organisation.roots[0].id
    },
    "ou1" : {
      "arn" : aws_organizations_organizational_unit.ou1.arn,
      "id" : aws_organizations_organizational_unit.ou1.id
    }
    #SSM_INSERT_BY_BAYAMI


  })
}
