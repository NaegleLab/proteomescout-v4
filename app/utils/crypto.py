import os
import hashlib

def __byteStringToHex(byteString):
    """
    Helper function utilized for converting byte strings into hex

    Parameters
    ----------
    byteString : bytes
        A byte string of any length
    
    Returns
    -------
    hexString : str
        A string of hex values representing the byte string after conversion
    """
    hexString = ''.join([hex(c)[2:].zfill(2) for c in byteString])
    return hexString

def randomString(size):
    """
    Creates a random string of hex values of a given size

    Parameters
    ----------
    size : int
        The desired size for the string
    
    Returns
    -------
    randString : str
        A randomly generated string of hex values
    """
    randString = __byteStringToHex(os.urandom(size))
    return randString

def generateActivationToken():
    return __byteStringToHex(os.urandom(25))

def generateSalt():
    """
    Creates a salt required for salting and safely storing passwords

    Returns
    -------
    salt : str
        A string of ten random hex values
    """
    salt = __byteStringToHex(os.urandom(5))
    return salt

def md5(clear_text):
    return hashlib.sha256(clear_text).hexdigest()

def saltedPassword(clear_password, salt = generateSalt()):
    """
    Takes in a provided password and encrypts it for safer storrage of private data
    
    Parameters
    ----------
    clear_password : str
        The unencrypted password provided by the user

    salt : str
        A string of ten random hex values. By default, it utilizes the generateSalt() function to automatically generate a salt values

    Returns
    -------
    salt : str
        A string of ten random hex values
        
    salted_password : str
        The encrypted password represented as a string of hex values
    """
    salted_password = hashlib.sha256((salt + clear_password).encode('utf-8')).hexdigest()
    return salt, salted_password
