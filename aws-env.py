# recommended version >= 3.8
import os
import subprocess 
from os import system as myConsole

operating_system=os.name
new_profile_name=""
mfaToken=""
mfaContent=""
myAccount=""
mySerial=""
profile_nane=""
sts_seconds="36000"
aws_username="giovanni.lauria"

MAX_MFA_LOOPS=3
MAX_ACCOUNT_LOOPS=3
ACCOUNT_NUMBER = [
    "865986445429      [dodi-login]",
    "794147387117      [docomo-digital]"
]
FOUND_SERIAL = False
FOUND_ACCOUNT = False
 
def UpdateCredentialsFile(credentials_file,_AWS_ACCESS_KEY_ID,_AWS_SECRET_ACCESS_KEY,_AWS_SESSION_TOKEN,_AWS_SESSION_EXPIRATION):
    _FOUND_MFA=False
    global new_profile_name
    new_profile_name=profile_name+"-mfa"
    lineCounter=0
    with open(credentials_file, 'r') as myFile:
        myFile.tell()           # store the pointer
        list_of_lines = myFile.readlines()
        myFile.seek(0)           # reset the pointer
        for myLine in myFile:
            lineCounter=lineCounter+1
            if new_profile_name in myLine:         
                _FOUND_MFA=True 
                break
    myFile.close()
    with open(credentials_file, 'w') as myFile:
        if not _FOUND_MFA:
            list_of_lines.insert(lineCounter,"["+ new_profile_name +"]\n")
            lineCounter=lineCounter+1   # since this line is written only if it has not found
            # we need to increment the pointer as we will have 1 more line
            list_of_lines.insert(lineCounter,"aws_access_key_id = "+_AWS_ACCESS_KEY_ID +"\n")            
            list_of_lines.insert(lineCounter+1,"aws_secret_access_key = "+_AWS_SECRET_ACCESS_KEY +"\n") 
            list_of_lines.insert(lineCounter+2,"aws_session_token = "+_AWS_SESSION_TOKEN +"\n") 
            list_of_lines.insert(lineCounter+3,"aws_session_expiration = "+_AWS_SESSION_EXPIRATION +"\n") 
            myFile.writelines(list_of_lines)    # modify the list and write to file the whole list
        else:
            list_of_lines[lineCounter]="aws_access_key_id = "+_AWS_ACCESS_KEY_ID +"\n"           
            list_of_lines[lineCounter+1]="aws_secret_access_key = "+_AWS_SECRET_ACCESS_KEY +"\n"
            list_of_lines[lineCounter+2]="aws_session_token = "+_AWS_SESSION_TOKEN +"\n"
            list_of_lines[lineCounter+3]="aws_session_expiration = "+_AWS_SESSION_EXPIRATION +"\n" 
            myFile.writelines(list_of_lines)    # modify the list and write to file the whole list

    myFile.close()

def AssumeRole(arn,session,profile):
    # This is only printing the command to issue
    myCommand="aws sts assume-role --role-arn '" + arn + "' --role-session-name " + session + " --profile=" + profile
    print("Issue this commamd in order to assumeRole:\n")
    print(myCommand)
 
retry_account=0
print ("Accounts available:")
for account in ACCOUNT_NUMBER:
    print(account)
retry_account=MAX_ACCOUNT_LOOPS
counter_while_len=0
while not FOUND_ACCOUNT and len(myAccount)!=12 and counter_while_len<3:
    myAccount=input("Copy the Account Number associated with the profile you want to login to (12 digits): ")
    if len(myAccount)==12:
        for account in ACCOUNT_NUMBER:
            if myAccount in account:
                FOUND_ACCOUNT=True
                break
    else:
        if not FOUND_ACCOUNT:
            counter_while_len+=1
            retry_account = MAX_ACCOUNT_LOOPS -counter_while_len
            print(str(retry_account) + " retries missing")
if FOUND_ACCOUNT:
    my_user_path = os.path.expanduser("~")
    if os.name == "posix":
        _folder_separator="/"
    else:
        _folder_separator="\\"
    credentials_file = my_user_path + _folder_separator + '.aws' + _folder_separator + 'credentials'
    config_file=my_user_path + _folder_separator + '.aws' + _folder_separator + 'config'
    print ("Profiles Available on " + credentials_file + ":")
    with open(credentials_file, 'r') as myFile:
        for myLine in myFile:
            if '[' in myLine and not 'mfa' in myLine:         # print the headers of the profiles only
                myLine=(myLine.replace("[",""))
                myLine=(myLine.replace("]",""))
                myLine=(myLine.replace("\n",""))
                print (myLine)
    myFile.close()
    profile_name=input("Enter the AWS configuration profile to use: ")

    if len(profile_name)==0:
        profile_name="default"
 
    with open(config_file, 'r') as myFile:
        myLine=myFile.readline()
        while myLine and not FOUND_SERIAL:
            if myAccount in myLine:
                FOUND_SERIAL = True
                mySerial="".join(myLine)
            else:
                myLine = myFile.readline()
    myFile.close()
    if not FOUND_SERIAL:   
        print ("Please set mfa_serial in " + config_file + " or check if it is correct.")
    else:  
        mfaToken=""
        retry_mfa=MAX_MFA_LOOPS
        counter_while_len=0
        while len(mfaToken)!=6 and counter_while_len<3:
            mfaToken=input("Enter your MFA Token for profile " + profile_name +" (6 digits only): ")
            if len(mfaToken)!=6:
                counter_while_len += 1
                retry_mfa = MAX_MFA_LOOPS - counter_while_len
                print(str(retry_mfa) + " retries missing")
 
        if retry_mfa!=0:
            AWS_ACCESS_KEY_ID=None
            AWS_SESSION_EXPIRATION=None
            AWS_SECRET_ACCESS_KEY=None
            AWS_SESSION_TOKEN=None
            AWS_SECURITY_TOKEN=None
         
            tmpSerial=("".join(mySerial.split("=")[1]).strip())
            myCommand='aws --profile=' + profile_name +' sts get-session-token --duration-seconds ' + sts_seconds + ' --serial-number ' + tmpSerial + ' --token-code '+ mfaToken +' --output text'
            p = subprocess.Popen(myCommand, stdout=subprocess.PIPE, shell=True) ## Talk with command i.e. read data from stdout and stderr. Store this info in tuple ##
            ## Interact with process: Send data to stdin. Read data from stdout and stderr, until end-of-file is reached. ##
         
            (output, err) = p.communicate() ## Wait for aws cli to terminate. Get return returncode ##
            p_status = p.wait()
            mfaContent=output.decode('utf-8').split("\t")
            if not p_status:
                AWS_ACCESS_KEY_ID=("".join(mfaContent[1]))
                AWS_SESSION_EXPIRATION=("".join(mfaContent[2]))
                AWS_SECRET_ACCESS_KEY=("".join(mfaContent[3]))
                AWS_SESSION_TOKEN=("".join(mfaContent[4])).rstrip("\n").rstrip("\r")
                AWS_SECURITY_TOKEN=("".join(mfaContent[4])).rstrip("\n").rstrip("\r")
                sessionName="training-" + aws_username
                UpdateCredentialsFile(credentials_file,AWS_ACCESS_KEY_ID,AWS_SECRET_ACCESS_KEY,AWS_SESSION_TOKEN,AWS_SESSION_EXPIRATION)         
                #AssumeRole("arn:aws:iam::661315133784:role/AdministratorAccess",sessionName,new_profile_name)       
                print("\nTemporary credentials set " + AWS_ACCESS_KEY_ID +" until " + AWS_SESSION_EXPIRATION)
                if os.name == "posix":
                    os.system('sed -i \'/AWS/d\' ~/.bashrc')  ## remove lines with AWS string in it
                    os.system('bash -c \'echo "export AWS_ACCESS_KEY_ID='+ AWS_ACCESS_KEY_ID +'" >> ~/.bashrc\'')
                    os.system('bash -c \'echo "export AWS_SECRET_ACCESS_KEY='+ AWS_SECRET_ACCESS_KEY  +'" >> ~/.bashrc\'')
                    os.system('bash -c \'echo "export AWS_SESSION_EXPIRATION='+ AWS_SESSION_EXPIRATION  +'" >> ~/.bashrc\'')
                    os.system('bash -c \'echo "export AWS_SESSION_TOKEN='+ AWS_SESSION_TOKEN  +'" >> ~/.bashrc\'')
                    os.system('bash -c \'echo "export AWS_SECURITY_TOKEN='+ AWS_SECURITY_TOKEN  +'" >> ~/.bashrc\'')
                    os.system('exec bash')
                else:
                    os.system("SETX {0} {1} /M".format("AWS_ACCESS_KEY_ID", AWS_ACCESS_KEY_ID))
                    os.system("SETX {0} {1} /M".format("AWS_SECRET_ACCESS_KEY", AWS_SECRET_ACCESS_KEY))
                    os.system("SETX {0} {1} /M".format("AWS_SESSION_EXPIRATION", AWS_SESSION_EXPIRATION))
                    os.system("SETX {0} {1} /M".format("AWS_SESSION_TOKEN", AWS_SESSION_TOKEN))
                    os.system("SETX {0} {1} /M".format("AWS_SECURITY_TOKEN", AWS_SECURITY_TOKEN))
                    print ("Keys are saved. Happy Coding!!!")
            else:
                print ("Error while connecting with MFA")
elif (not FOUND_ACCOUNT):
    print ("The specified account has not been found")
    print ("Exiting")
else:
    print ("No account has been selected")
    print ("Exiting")
input("Press any key to exit...")

