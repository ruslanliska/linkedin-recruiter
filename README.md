## **Prerequisites**

Before you begin, ensure you have the following installed on your system:

- **Python 3.x**: Download and install from [python.org](https://www.python.org/downloads/). During installation, check the option to **Add Python to PATH**.
- **Git** (optional): If you prefer cloning the repository instead of downloading the ZIP file, install Git from [git-scm.com](https://git-scm.com/downloads).
- **Google Chrome**: The project may interact with Chrome; download it from [google.com/chrome](https://www.google.com/chrome/).

---

## **Step-by-Step Instructions**

### **1. Download the Project**

You have two options to get the project files: cloning the repository or downloading it as a ZIP file.

#### **Option A: Clone the Repository Using Git**

1. **Open PowerShell**:

   - Press `Win + X` and select **Windows PowerShell** or **Windows PowerShell (Admin)**.

2. **Navigate to Your Desired Directory**:

   ```powershell
   cd C:\path\to\your\desired\directory
   ```

   - Replace `C:\path\to\your\desired\directory` with the path where you want to place the project folder.

3. **Clone the Repository**:

   ```powershell
   git clone https://github.com/ruslanliska/linkedin-recruiter.git
   ```

   - This command creates a folder named `linkedin-recruiter` in your current directory.

#### **Option B: Download as ZIP**

1. **Download the ZIP File**:

   - Visit the repository: [https://github.com/ruslanliska/linkedin-recruiter](https://github.com/ruslanliska/linkedin-recruiter).
   - Click on the green **Code** button and select **Download ZIP**.

2. **Extract the ZIP File**:

   - Right-click the downloaded ZIP file and select **Extract All**.
   - Choose the destination folder where you want the project files.

### **2. Navigate to the Project Root Directory**

In PowerShell, navigate to the root directory of the project:

```powershell
cd C:\path\to\linkedin-recruiter
```

- Replace `C:\path\to\linkedin-recruiter` with the actual path to the project folder.

### **3. Adjust PowerShell Execution Policy**

To allow the execution of the setup script, adjust the execution policy for the current session:

```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
```

- **Explanation**: This command temporarily bypasses the execution policy restrictions for the current PowerShell session, allowing you to run unsigned scripts like `setup.ps1`.

### **4. Run the Setup Script**

Execute the setup script to set up the project environment:

```powershell
.\setup.ps1
```

- **What This Does**:
  - Checks for Python installation.
  - Creates a virtual environment named `venv` if it doesn't exist.
  - Activates the virtual environment.
  - Upgrades `pip` to the latest version.
  - Installs required Python packages from `requirements.txt`.
  - Runs the Chrome setup script (`src/setup_chrome.py`) if it exists.

- **Possible Prompts**:
  - If prompted to install packages or confirm actions, type `Y` and press **Enter**.

### **5. Add the `.env` File with Your OpenAI API Key**

Create a `.env` file in the project root directory to store your OpenAI API key.

#### **Create the .env File**

```powershell
New-Item -ItemType File -Path .\.env
```

#### **Edit the .env File**

1. **Open the .env File**:

   ```powershell
   notepad .\.env
   ```

2. **Add Your OpenAI API Key**:

   In the Notepad window that opens, type the following line:

   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

   - Replace `your_openai_api_key_here` with your actual OpenAI API key.

3. **Save and Close Notepad**:

   - Click **File** > **Save**, then close Notepad.

### **6. Run the Project**

Execute the main script to start the application:

```powershell
.\run.ps1
```

- **What This Does**:
  - Activates the virtual environment.
  - Runs the main application script (e.g., `src/main.py` or similar, depending on the project's structure).

---

## **Full Command Sequence**

Here's the complete set of commands for quick reference:

```powershell
# Navigate to the project directory
cd C:\path\to\linkedin-recruiter

# Adjust execution policy for the current session
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process

# Run the setup script
.\setup.ps1

# Create the .env file
New-Item -ItemType File -Path .\.env

# Add your OpenAI API key to the .env file
notepad .\.env
# In Notepad, add: OPENAI_API_KEY=your_openai_api_key_here
# Save and close Notepad

# Run the project
.\run.ps1
```

---

## **Additional Information**

### **Virtual Environment**

- **Purpose**: The virtual environment ensures that the project's Python dependencies are isolated from other Python projects on your system.
- **Activation**: The `setup.ps1` and `run.ps1` scripts handle the activation of the virtual environment automatically.

### **Python Packages**

- **Dependencies**: Listed in `requirements.txt`.
- **Installation**: Handled by the `setup.ps1` script using `pip`.

### **Chrome Setup**

- **Script**: `src/setup_chrome.py`
- **Function**: Configures the Chrome WebDriver needed for automation tasks.
- **Requirement**: Ensure you have Google Chrome installed.

### **Environment Variables**

- **File**: `.env`
- **Usage**: Stores sensitive information like API keys without hardcoding them into scripts.
- **Security**: Do not commit the `.env` file to version control systems like Git.

---

## **Troubleshooting**

### **Execution Policy Error**

- **Issue**: Error message stating scripts cannot be run due to execution policy.
- **Solution**: Ensure you've run `Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process`.

### **Python Not Recognized**

- **Issue**: Error stating `python` is not recognized as a command.
- **Solution**:
  - Verify Python is installed.
  - Ensure Python is added to the system PATH.
  - Close and reopen PowerShell after installation.

### **Permission Denied Errors**

- **Issue**: Access is denied when running scripts.
- **Solution**:
  - Run PowerShell as an administrator.
  - Right-click on PowerShell and select **Run as administrator**.

### **Missing Dependencies**

- **Issue**: Errors about missing Python packages.
- **Solution**:
  - Ensure `setup.ps1` completed successfully.
  - Manually install packages:

    ```powershell
    .\venv\Scripts\Activate.ps1
    python -m pip install -r requirements.txt
    ```

### **API Key Errors**

- **Issue**: Application fails due to missing or incorrect API key.
- **Solution**:
  - Double-check the `.env` file.
  - Ensure there are no extra spaces or characters.
  - Verify that your OpenAI API key is active and has the necessary permissions.

### **Virtual Environment Activation Failure**

- **Issue**: Scripts can't activate the virtual environment.
- **Solution**:
  - Check if the `venv` folder exists.
  - Manually activate the virtual environment:

    ```powershell
    .\venv\Scripts\Activate.ps1
    ```

---

## **Security Considerations**

- **Execution Policy**: Changing the execution policy to `Bypass` lowers your system's security for the session. Only do this when running trusted scripts.
- **Resetting Execution Policy**: After you're done, you can close the PowerShell session, or reset the execution policy:

  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy Restricted -Scope Process
  ```

- **API Keys**: Keep your `.env` file secure. Do not share your API key or commit it to any repositories.

---

## **Summary**

By following these steps, you will:

- Obtain the project files.
- Configure your environment to run PowerShell scripts.
- Set up the Python virtual environment and install dependencies.
- Provide the necessary API key for OpenAI services.
- Run the application successfully.

---

## **Need Further Assistance?**

If you encounter any issues or have questions:

- **Check the Project's README**: There may be additional instructions or updates.
- **GitHub Issues**: Look for existing issues or open a new one on the project's GitHub page.
- **Contact the Developer**: Reach out to the project maintainer for support.
