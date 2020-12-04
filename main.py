import xlrd
import yaml
import os.path
from copy import deepcopy

template_a = """resource "aws_organizations_organizational_unit" "{ou}" {obrace}
  name      = "${obrace}local.account_prefix{cbrace}-ou-{ou}"
  parent_id = aws_organizations_organization.organisation.roots[0].id
  
"""

template_b = """    "{ou}" : {obrace}
      "arn" : aws_organizations_organizational_unit.{ou}.arn,
      "id" : aws_organizations_organizational_unit.{ou}.id
    {cbrace}
"""

yaml_data = []
yml = {}

loc = ("src/input.xlsx")
wb = xlrd.open_workbook(loc)
sheet = wb.sheet_by_index(0)


#this function appends ou details to existing org.tf file
def write_org_file(ou_str):
    with open("src/org.tf", "r") as in_file:
        buf = in_file.readlines()

    with open("src/org.tf", "w") as out_file:
        for line in buf:
            out_file.write(line)
            if line.strip().startswith('#OU_INSERT_BY_BAYAMI'):
                print("writing ou..")
                out_file.write(template_a.format(ou=ou_str, obrace="{", cbrace="}" ))

            if line.strip().startswith('#SSM_INSERT_BY_BAYAMI'):
                print("writing ssm..")
                out_file.write(template_b.format(ou=ou_str, obrace="{", cbrace="}" ))


#this function creates/appends accounts_map.yaml file
def write_accnts_map(yaml_data):
    if os.path.isfile("src/accounts_map.yaml"):
        print("File exist, appending..")
        with open("src/accounts_map.yaml", "a") as out_file:
            stream = yaml.dump(yaml_data, sort_keys=False)
            stream_nq = stream.replace('\'', '')
            stream_nl = stream_nq.replace('- ', '\n- ')
            out_file.write(stream_nl)

    else:
        print("File not exist, creating new file..")
        with open("src/accounts_map.yaml", "w") as out_file:
           out_file.write("accounts:")
           stream = yaml.dump(yaml_data, sort_keys=False)
           stream_nq = stream.replace('\'', '')
           stream_nl = stream_nq.replace('- ', '\n- ')
           out_file.write(stream_nl)


def main():

    # get all values in the col 0  - populate ou entries
    for ou_entry in sheet.col_values(0, start_rowx=1):
        print("ou entry={}".format(ou_entry))
        write_org_file(ou_entry)

    # get the row values, populate yaml file entries here
    for row in range(sheet.nrows):
        if row != 0:
            row_list = sheet.row_values(row)
            print(row_list)
            yml.clear()
            yml['name'] = row_list[1]
            yml['type'] = row_list[2]
            yml['alias'] = 'aws-predemo2-' + row_list[1]
            yml['email'] = 'aws-predemo2-' + row_list[1] + '@sourcedgroup.com'
            yml['parentou'] = row_list[0]

            # check if baselne_config is set
            if row_list[3] == 1:
                print('baseline_config is set')
                # create nested dict
                yml['baseline_config'] = {}
                if row_list[4] == 1:
                    yml['baseline_config']['is_logging_account'] = 'true'
                if row_list[5] == 1:
                    yml['baseline_config']['is_compliance_account'] = 'true'
                if row_list[6] == 1:
                    yml['baseline_config']['is_egress_account'] = 'true'
                if row_list[7] == 1:
                    yml['baseline_config']['create_vpc'] = 'true'
                    yml['baseline_config']['vpc_cidr'] = row_list[8]

            # use deepcopy to ignore anchors/aliases - &id001 *id001
            yml_c = deepcopy(yml)
            yaml_data.append(yml_c)

    # loaded all yaml values, write to file
    write_accnts_map(yaml_data)

if __name__ == "__main__":
    main()
