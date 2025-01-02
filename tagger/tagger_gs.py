import GoogleSheet as gs
import boto3
import boto3.session
import json


class awsResources:
    def __init__(self, profile, type):
        self.session = boto3.Session(profile_name=profile)
        self.resource = self.session.resource(type)


def get_aws_resources(session, tags, cloud):
    instances = []
    ec2 = session.resource("ec2")
    for i in ec2.instances.all():
        instance = [
            i.id,
            i.private_ip_address,
            cloud,
            i.key_name,
            i.state["Name"],
            i.instance_type,
            i.placement["AvailabilityZone"],
            "",
        ]
        basecount = len(instance)
        try:
            for key in tags[basecount:]:
                value = ""
                for tag in i.tags:

                    if tag["Key"] == key:

                        value = tag["Value"]
                instance.append(value)
        except Exception as e:
            print(e)
        instances.append(instance)
    return instances


def search(item, values):
    for x in values:
        if item[0] == x[0]:
            return values.index(x)
    return None


def main():

    with open("Files/Config.json") as config_file:
        Config = json.load(config_file)

    profiles = Config["profiles"]
    spredsheet_id = Config["spredsheet_id"]
    headers = Config["headers"]
    pull = input("Write tags to GoogleSheet (y/n): ") == "y"
    push = input("Write tags to aws (y/n): ") == "y"
    dryrun = False

    for profile in profiles:
        print(f"------------{profile}------------")
        try:
            session = boto3.Session(profile_name=profile)
        except Exception as e:
            print(e)
            continue
        sheet = gs.GoogleSheet("Master", id=spredsheet_id, baserange=profile)
        instances = get_aws_resources(session, headers)

        print(f"https://docs.google.com/spreadsheets/d/{sheet.get_id()}/edit#gid=0")

        if pull:
            sheet.clear_sheet(headers, instances)
            sheet.sheet_write(headers, instances)
        else:
            sheet.calc_range(headers)

        if push:
            updated_instances = sheet.sheet_read()
            for inst in updated_instances[1:]:
                size = len(inst)
                updated_tags = []
                index = search(inst, instances, profile)

                if index is None or inst[0] == "":
                    print(f"No updated tags for {inst[0]}")
                else:
                    for x in range(1, size):
                        if inst[x] != instances[index][x]:
                            print(f"{headers[x]} added to {inst[0]}")
                            updated_tags.append({"Key": headers[x], "Value": inst[x]})

                    if dryrun is False:
                        if updated_tags != []:
                            try:
                                instance = ec2.Instance(inst[0])
                                instance.create_tags(Tags=updated_tags)
                            except Exception as e:
                                print(f"failed to Write tags to {inst[0]} -- {e}")
                            print(f"Write tags to {inst[0]}")
                            for tag in updated_tags:
                                print(tag)
                    else:
                        print(f"Pretending to Write tags to {inst[0]}")
                        for tag in updated_tags:
                            print(tag)


if __name__ == "__main__":
    main()
