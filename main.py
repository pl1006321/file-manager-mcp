from mcp.server.fastmcp import FastMCP
import os
import mimetypes
from pypdf import PdfWriter, PdfReader
import fnmatch
from playwright.async_api import async_playwright
from urllib.parse import urlparse
from datetime import date
import asyncio

mcp =  FastMCP('file manager!')

@mcp.tool()
async def web_to_pdf(url: str, file_name: str=None, dir_name: str='/Downloads') -> str:
    """
    creates a locally saved pdf of a specified webpage. 

    params:
        url (str): a url to a valid webpage. must include the https header. 
        file_name (str): the output file name that the pdf will be saved as. defaults to the domain name if not specified. 
        dir_name (str): the directory that the user wishes to save the file to. must start with /

    returns:
        str: a string indicating whether or not the pdf has been saved successfully. 
    """
    if file_name is None:
        date_str = date.today().strftime('%m%d%Y') # create string of date with format MMDDYYYY
        # parse url and extract the domain name without the tld 
        print(urlparse(url))
        file_name = urlparse(url)[1].split('.')[-2] + '_snapshot_' + date_str + '.pdf'
        # an example result of output would be google_snapshot_07302025 

    file_path = os.path.join(os.path.expanduser('~'), dir_name.lstrip('/'))
    full_path = os.path.join(file_path, file_name)
    # print(f'file path: {file_path} \nfull_path: {full_path}')

    async with async_playwright() as p:
        
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)
        await page.pdf(path=full_path)
        await browser.close()

    return f'{url} has been saved successfully to {file_path} as {file_name}'

@mcp.tool()
def get_file_path(file_name: str, extension: str=None) -> str:
    """
    finds the full file path if searching for a specific file.
    supports wildcard characters like * and ?. 
    * can represent any number of unknown characters
        e.g test_abc.pdf can be found if searching for test_*.pdf 
    ? can only represent one character at a time
        e.g test_a.pdf can be found if searching for test_?.pdf 

    params:
        file_name (str): the name of the file. supports wildcard characters
        extension (str): file extension (with the dot) e.g .pdf, .txt, .docx
            -> defaults to None if not specified 
    
    returns:
        str: full file path name if found, otherwise returns an empty string
    """
    user_dir = os.path.expanduser("~")  
    

    for root, dirs, files in os.walk(user_dir):
        for file in files:
            # check if extension filter is specified
            if extension and not file.endswith(extension):
                continue
            
            # check if file matches search content
            if fnmatch.fnmatch(file.lower(), ''.join([file_name.lower(), extension])):
                return os.path.abspath(os.path.join(root, file))
    
    # return an empty string if file was not found 
    return ""

@mcp.tool()
def password_protect_pdf(input_path: str, password: str, output_path: str=None,) -> str: 
    """
    applies a password onto a pdf.

    parameters: 
        file_name (str): input file path
        password (str): the password added onto the pdf file.
        output_path (str): output file path. set to the same as file_name as default

    returns:
        str: a message indicating the end result 
    """
    if output_path is None:
        output_path = input_path
    
    try:
        reader = PdfReader(input_path)
        writer = PdfWriter() 

        for page in reader.pages:
            writer.add_page(page)
        
        writer.encrypt(password)

        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
    
        return 'the file has been successfully protected'
    except Exception as e:
        print(f'exception has occurred: {e}')

@mcp.tool()
def check_file_integrity(file_path: str) -> dict:
    """
    applies multiple basic file integrity checks on a specified file. 

    parameters:
        file_path (str): input file path

    returns:
        str: a message indicating the end result
    """
    checks = {
        'exists': False,
        'readable': False,
        'non_empty': False,
        'size': 0,
        'mime_type': None,
        'extension_matches': False
    }

    if not os.path.exists(file_path):
        return checks # return as is, since the file does not exist 
    checks['exists'] = True # if it exists, mark it as so

    try:
        with open(file_path, 'rb') as f:
            f.read(1) # checks if file is readable 
        checks['readable'] = True
    except (IOError, PermissionError):
        return checks

    checks['size'] = os.path.getsize(file_path)
    checks['non_empty'] = checks['size'] > 0

    try:
        checks['mime_type'], _ = mimetypes.guess_type(file_path)
        
        # check if extension matches mime type 
        extension = os.path.splitext(file_path)[1].lower()
        extensions = {
            'image/jpeg': ['.jpg', '.jpeg'],
            'image/png': ['.png'],
            'application/pdf': ['.pdf'],
            'text/plain': ['.txt'],
            # Add more as needed
        }

        expected_ext = extensions.get(checks['mime_type'], [])
        checks['extension_matches'] = extension in expected_ext or not expected_ext

    except:
        pass

    print(checks['mime_type'])
    print(extension)
    return checks