# gpgmsg.py
#
# I am writing this script to allow myself to more easily respond to
# messages that are sent to me via GPG encrypted files.

import gnupg
import os
import sys
import getpass
import re

# Global variables
_gpg = None
_gnupg_home_dir = ""


def setup_config():
    """Sets up the configuration for the script.

    If this script is being run for the first time it sets up the
    configuration to defaults. If it has been run before it loads
    the configs from the config file.
    """
    conf_file = os.path.expanduser("~/.gpgmsg/gpgmsg.conf")
    gnupg_conf_dir = os.path.expanduser("~/.gpgmsg/gnupg/")

    if not os.path.exists(conf_file):
        # Initial config required.
        os.makedirs(os.path.dirname(conf_file))

        conf_string = """GNUPG_HOME_DIR,~/.gpgmsg/gnupg/
"""

        f = open(conf_file, "w")
        f.write(conf_string)
    conf = open(conf_file, "r")
    # Read in the configuration.

    for line in conf:
        line = line.strip().split(',')
        if not len(line) == 2:
            next
        else:
            # Read in the GNUPG home directory. Used to load keys etc
            if line[0] == "GNUPG_HOME_DIR":
                global _gnupg_home_dir
                _gnupg_home_dir = line[1]
                # If the path is relative to the home dir, expand it.
                if re.match("^~", _gnupg_home_dir):
                    print "[+] Expanding _gnupg_home_dir"
                    _gnupg_home_dir = os.path.expanduser(_gnupg_home_dir)

                # Create the directory if it doesn't exist.
                if not os.path.exists(_gnupg_home_dir):
                    print "[+] Directory does not exist. Creating"
                    os.mkdir(_gnupg_home_dir)


def gpg_conf():
    """Creates the global gnupg object used by other functions."""
    global _gpg
    if not _gnupg_home_dir:
        print "[!] ERROR: gpg_conf: no _gnupg_home_dir specified"
        sys.exit(-1)

    _gpg = gnupg.GPG(gnupghome=_gnupg_home_dir)


def gpg_decrypt(crypt_text, pphrase):
    """Return decrypted plaintext.

    Required Arguments:
    crypt_text - gpg encrypted data to decrypt
    pphrase - the private key passphrase to be used when decrcypting
    """
    # Kill the script if data is omitted
    if crypt_text == "" or pphrase == "":
        print "[!] ERROR: gpg_decrypt: missing crypt_text or passphrase"
        sys.exit(-1)

    # Time to decrypt!
    dec_obj = _gpg.decrypt(crypt_text, passphrase=pphrase)

    if not dec_obj.ok:
        print "[!] ERROR: gpg_decrypt: Failed to decrypt message"
        print dec_obj.stderr
        sys.exit(-1)

    return dec_obj.data


def gpg_encrypt(message_text, email):
    """Return encrypted message text.

    Required Arguments:
    message_text - text to encrypt
    email - email address associated with the public key that should be used
            to encrypt the message
    """
    # Kill the script if data is omitted
    if message_text == "" or email == "":
        print "[!] ERROR: gpg_encrypt: missing message_text or email"
        sys.exit(-1)

    # Time to encrypt! Yea baby!
    enc_obj = _gpg.encrypt(message_text, email, always_trust=True)

    if not enc_obj.ok:
        print "[!] ERROR: gpg_encrypt: Failed to encrypt message"
        print enc_obj.stderr
        sys.exit(-1)

    return str(enc_obj)


def gpg_import_key(file_contents):
    """Import a gpg key for later use.

    Required Arguments:
    file_contents - text from the key file to import
    """
    # Kill the script if data is omitted
    if file_contents == "":
        print "[!] ERROR: gpg_import_key: missing file_name"
        sys.exit(-1)

    print "file_contents length: " + str(len(file_contents))
    # Time to get crackin' on the key import! Heeyaw!
    import_result = _gpg.import_keys(file_contents)

    if import_result.count == 0:
        print "[!] ERROR: gpg_import_key: No keys imported"
        print import_result.stderr
        sys.exit(-1)
    else:
        return True


def gpg_pub_key_emails():
    """Return a list of emails associated with public keys in the store."""
    return _gpg.list_keys()


def normalize_filename(filename, must_exist=True):
    """Return normalized absolute path to file.

    Required Arguments:
    filename - name of the file to verify and/or expand to the absolute path

    Optional Arguments:
    must_exist - boolean flag to determine if the file must exist already in
                 order for the function to return successfully
    """
    if filename == "":
        print "[!] ERROR: normalize_filename: Invalid filename"
        sys.exit(-1)

    if not type(must_exist) is bool:
        print "[!] ERROR: normalize_filename: Parameter 'must_exist'" +\
              " must be boolean"
        sys.exit(-1)

    if re.match("^~/", filename):
        print "[+] Expanding ~ to absolute path"
        filename = os.path.expanduser(filename)
    elif not os.path.isabs(filename):
        print "[+] Generating absolute path"
        filename = os.path.join(os.getcwd(), filename)

    # Time to check if we need to ensure the file exists before returning
    # the path and return
    # the path as appropriate
    if not must_exist:
        return filename
    else:
        if not os.path.exists(filename):
            return None
        else:
            return filename


def reply(orig_msg):
    """Return hierarchical message history.

    Required Arguments:
    orig_msg - message that the user input is replying to

    The user will be prompted for input until they send a period only on a
    line. The message they're replying to has '> ' added to the
    beginning of each line and the new message prepended to it all, making
    a hierarchical conversation.

    Ex:

    Hey. I'm responding to your message.

    > Hey. This is my message. Please respond to me!
    """
    if orig_msg == "":
        print "[!] ERROR: reply: Parameter 'orig-msg' is required"
        sys.exit(-1)

    print "[+] Replying (End with . on a newline):"
    new_msg = ""

    while True:
        data = raw_input("> ")
        if data == ".":
            break
        else:
            new_msg += data + "\n"

    new_msg += "\n\n"
    # Add the > to the each line of orig_msg and add it to the new message
    for line in orig_msg.strip().split("\n"):
        new_msg += "> " + line + "\n"

    return new_msg


def dec_and_read_file(filename="", passphrase=""):
    """Return decrypted text.

    Optional Arguments:
    file - name of the file to decrypt. user will be prompted if left blank
    passphrase - private key passphrase used to decrypt. user will be prompted
                 if left blank
    """
    if filename == "":
        filename = raw_input("[>] File to decrypt: ")

        if filename == "":
            print "[!] ERROR: dec_and_read_file: Filename cannot be blank"
            sys.exit(-1)

    filename = normalize_filename(filename)

    print "[+] Reading encrypted file: " + filename
    enc_data = open(filename, "r").read()

    # Prompt for the passphrase if it was not provided
    if passphrase == "":
        passphrase = getpass.getpass("[>] Decryption passphrase: ")

        if passphrase == "":
            print "[!] ERROR: dec_and_read_file: Decryption passphrase " +\
                  "cannot be blank"
            sys.exit(-1)

    data = gpg_decrypt(enc_data, passphrase)

    return data


def enc_and_write_to_file(message, default_file=""):
    """Encrypt a message and save it to a file.

    Required Arguments:
    message - message to encrypt

    Optional Arguments:
    default_file - file to write to if the user doesn't input one
    """
    if message == "":
        print "[!] ERROR: enc_and_write_to_file: Parameter 'message'" +\
              " is required"
        sys.exit(-1)

    # Build the prompt based on if there is a default file specified
    prompt = "[>] Write to file"
    if default_file == "":
        prompt += ": "
    else:
        prompt += " (" + default_file + "): "

    # Get the file to write to.
    filename = raw_input(prompt)

    if filename == "" and not default_file == "":
        filename = default_file

    # Make sure the filename is absolute
    filename = normalize_filename(filename, must_exist=False)

    # Get the email address to encrypt for
    email = raw_input("[>] Email to encrypt for: ")

    if email == "":
        print "[!] ERROR: enc_and_write_to_file: Email cannot be blank"

    print "[+] Encrypting message for " + email
    # Encrypt the message
    enc_msg = gpg_encrypt(message, email)

    if re.match("^\[!\] ERROR:", enc_msg):
        print enc_msg
        sys.exit(-1)

    print "[+] Writing message to " + filename
    # Write to the file
    w_file = open(filename, "w").write(enc_msg)

#
# Main Program Loop
#
print "[+] Loading config"
setup_config()
print "[+] Configuring gnupg"
gpg_conf()
if _gpg is None:
    print "[!] ERROR: Main loop: _gpg is None"
    sys.exit(-1)
# Begin prompt loop
while 1:
    print """
########## Menu ##########
[1] Import Key
[2] Decrypt Message
[3] Exit"""
    options = raw_input("[>] ")

    if options == "1":
        print "[+] Importing key"
        key_file = raw_input("[>] Key file: ")
        key_file = normalize_filename(key_file)
        if key_file is None:
            print "[!] ERROR: File does not exist"
            break

        print "[+] Found: " + key_file
        key_data = open(key_file, "r").read()

        if len(key_data) == 0:
            print "[!] ERROR: File " + msg_file + " exists but is empty"
            break

        gpg_import_key(key_data)
        print "[+] Import successful"

    elif options == "2":
        dec_file = raw_input("[>] File to decrypt: ")
        dec_msg = dec_and_read_file(filename=dec_file)
        print "[+] Decrypted message:"
        print dec_msg

        # Ask if the user would like to respond
        respond = raw_input("[>] Respond? (Y/n): ").lower()

        if respond == "n":
            print "[+] Not responding"
            break
        elif respond == "y" or respond == "":
            print "[+] Responding"
        else:
            print "[!] ERROR: Invalid input"
            break

        reply_body = reply(dec_msg)

        enc_and_write_to_file(reply_body, default_file=dec_file)

    elif options == "3":
        print "[+] Quitting..."
        sys.exit(0)
    else:
        print "[?] Invalid option"
