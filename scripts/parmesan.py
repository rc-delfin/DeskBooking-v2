import boto3
from botocore.exceptions import ClientError


class ParameterNotFound(Exception):
    """Raised when parameter is not found in the parameters list"""

    pass


class AWSparms:
    def __init__(self, path, access_key=None, secret=None, decrypt=False):
        try:
            if access_key is None and secret is None:
                ssm = boto3.client(
                    "ssm",
                    region_name="ap-southeast-1",
                )
            else:
                ssm = boto3.client(
                    "ssm",
                    region_name="ap-southeast-1",
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret,
                )

        except ClientError as e:
            print(e.response["Error"]["Code"])

        except Exception as err:
            print(err)
            print("error on service ssm using specified credentials")

        else:
            response = ssm.get_parameters_by_path(
                Path=path, Recursive=False, WithDecryption=decrypt
            )
        self.parmlist = response["Parameters"]

    def get_parm(self, parm_name, isString=True):
        retval = None
        try:
            for p in self.parmlist:
                if parm_name in p["Name"]:
                    retval = p["Value"]
                    break
            if retval is None:
                raise ParameterNotFound

        except ParameterNotFound:
            print(
                f"error on parameter name {parm_name} not found in parameter list {self.parmlist}"
            )

        return retval if isString else int(retval)
