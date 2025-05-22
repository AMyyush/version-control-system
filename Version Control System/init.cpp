#include <iostream>
#include <windows.h>
#include <direct.h>
#include <string>
#include <fstream>
#include <ctime>

using namespace std;

// Function to create a directory
bool createDirectory(const string &path) {
    if (GetFileAttributes(path.c_str()) == INVALID_FILE_ATTRIBUTES) {
        if (_mkdir(path.c_str()) == 0) {
            cout << "Created: " << path << endl;
            return true;
        } else {
            cerr << "Failed to create: " << path << endl;
            return false;
        }
    } else {
        cout << "Repository already exists: " << path << endl;
        return false;
    }
}

// Function to add a file to the repository
bool addFile(const string &repoDir, const string &filename) {
    string sourcePath = filename;
    string destPath = repoDir + "\\" + filename;

    // Check if the source file exists
    ifstream srcFile(sourcePath);
    if (!srcFile) {
        cout << "File not found: " << sourcePath << endl;

        char createFileChoice;
        cout << "Do you want to create this file? (y/n): ";
        cin >> createFileChoice;

        if (createFileChoice == 'y' || createFileChoice == 'Y') {
            // Create the file if it doesn't exist
            ofstream newFile(sourcePath);
            if (newFile) {
                cout << "File created: " << sourcePath << endl;
                newFile.close();
                return addFile(repoDir, filename); // Retry adding after creation
            } else {
                cerr << "Failed to create file: " << sourcePath << endl;
                return false;
            }
        } else {
            cout << "File not added to the repository." << endl;
            return false;
        }
    }

    // Copy file to repository
    ofstream destFile(destPath);
    if (destFile) {
        destFile << srcFile.rdbuf();
        cout << "File added: " << filename << endl;
        return true;
    } else {
        cerr << "Failed to add file: " << filename << endl;
        return false;
    }
}

// Function to commit a file with a timestamp
bool commitFile(const string &repoDir, const string &filename) {
    string commitDir = repoDir + "\\commits";
    string commitFileName = commitDir + "\\" + filename;

    // Create commit directory if it doesn't exist
    if (GetFileAttributes(commitDir.c_str()) == INVALID_FILE_ATTRIBUTES) {
        _mkdir(commitDir.c_str());
    }

    // Get timestamp for commit version
    time_t now = time(0);
    char timestamp[20];
    strftime(timestamp, sizeof(timestamp), "%Y%m%d%H%M%S", localtime(&now));
    string commitVersionFile = commitFileName + "." + timestamp;

    // Read the file content
    string filePath = repoDir + "\\" + filename;
    ifstream srcFile(filePath);
    if (!srcFile) {
        cerr << "Error: File not found for commit at: " << filePath << endl;
        return false;
    }

    // Write the commit version to the commit directory
    ofstream destFile(commitVersionFile);
    if (destFile) {
        destFile << srcFile.rdbuf();
        cout << "File committed: " << commitVersionFile << endl;
        return true;
    } else {
        cerr << "Failed to commit file: " << filename << endl;
        return false;
    }
}

// Function to revert a file to a specific version
bool revertFile(const string &repoDir, const string &filename, const string &timestamp = "") {
    string commitDir = repoDir + "\\commits";
    string targetFile;

    WIN32_FIND_DATA findFileData;
    HANDLE hFind = FindFirstFile((commitDir + "\\" + filename + ".*").c_str(), &findFileData);

    if (hFind == INVALID_HANDLE_VALUE) {
        cerr << "No commits found for file: " << filename << endl;
        return false;
    }

    // Search for the matching commit file
    do {
        if (findFileData.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) continue;

        string foundFile = findFileData.cFileName;
        if (foundFile.substr(0, filename.length()) == filename) {
            if (!timestamp.empty()) {
                // If timestamp is provided, match the file
                if (foundFile == filename + "." + timestamp) {
                    targetFile = foundFile;
                    break;
                }
            } else {
                // Otherwise, select the latest version
                if (targetFile.empty() || foundFile > targetFile) {
                    targetFile = foundFile;
                }
            }
        }
    } while (FindNextFile(hFind, &findFileData) != 0);
    FindClose(hFind);

    if (targetFile.empty()) {
        cerr << "No matching commit found for file: " << filename << endl;
        return false;
    }

    // Copy the file content back to the working directory
    string commitFilePath = commitDir + "\\" + targetFile;
    string filePath = repoDir + "\\" + filename;
    ifstream commitFile(commitFilePath);
    if (!commitFile) {
        cerr << "Error: Commit file not found at: " << commitFilePath << endl;
        return false;
    }

    ofstream destFile(filePath);
    if (destFile) {
        destFile << commitFile.rdbuf();
        cout << "File reverted to: " << targetFile << endl;
        return true;
    } else {
        cerr << "Failed to revert file: " << filename << endl;
        return false;
    }
}

// Main function for the command-line interface
int main(int argc, char* argv[]) {
    string repoDir = "MyRepo"; // Repository directory

    if (argc < 2) {
        cerr << "Usage:\n";
        cerr << "  myvcs init\n";
        cerr << "  myvcs add <filename>\n";
        cerr << "  myvcs commit <filename>\n";
        cerr << "  myvcs revert <filename> [timestamp]\n";
        return 1;
    }

    string command = argv[1];

    if (command == "init") {
        if (createDirectory(repoDir)) {
            cout << "Initialized empty VCS repository in " << repoDir << "\\" << endl;
        }
    } else if (command == "add" && argc >= 3) {
        string filename = argv[2];
        if (addFile(repoDir, filename)) {
            cout << "File " << filename << " added to repository." << endl;
        }
    } else if (command == "commit" && argc >= 3) {
        string filename = argv[2];
        if (commitFile(repoDir, filename)) {
            cout << "File " << filename << " committed." << endl;
        }
    } else if (command == "revert" && argc >= 3) {
        string filename = argv[2];
        string timestamp = (argc == 4) ? argv[3] : "";
        if (revertFile(repoDir, filename, timestamp)) {
            cout << "File " << filename << " reverted." << endl;
        }
    } else {
        cerr << "Invalid command or missing arguments.\n";
    }

    return 0;
}
