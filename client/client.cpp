// Simple C++ client for file upload
// Requires C++17 or later and libcurl
#include <iostream>
#include <fstream>
#include <string>
#include <curl/curl.h>
#include <chrono>
#include <iomanip>
#include <sstream>

// Callback function for progress updates
static int progress_callback(void *clientp, curl_off_t dltotal, curl_off_t dlnow, curl_off_t ultotal, curl_off_t ulnow) {
    if (ultotal == 0) return 0; // Avoid division by zero
    
    int percentage = static_cast<int>((ulnow * 100) / ultotal);
    std::cout << "\rUploading: " << percentage << "% [";
    
    int barWidth = 30;
    int pos = barWidth * percentage / 100;
    for (int i = 0; i < barWidth; ++i) {
        if (i < pos) std::cout << "=";
        else if (i == pos) std::cout << ">";
        else std::cout << " ";
    }
    std::cout << "] " << ulnow << "/" << ultotal << " bytes" << std::flush;
    
    return 0; // Continue transfer
}

int main(int argc, char* argv[]) {
    if (argc != 5) {
        std::cerr << "Usage: " << argv[0] << " <server_url> <username> <password> <file_path>\n";
        return 1;
    }
    std::string url = argv[1];
    std::string username = argv[2];
    std::string password = argv[3];
    std::string file_path = argv[4];

    std::ifstream file(file_path, std::ios::binary);
    if (!file) {
        std::cerr << "Failed to open file: " << file_path << std::endl;
        return 1;
    }
    file.seekg(0, std::ios::end);
    size_t filesize = file.tellg();
    file.seekg(0, std::ios::beg);
    std::string filedata(filesize, '\0');
    file.read(&filedata[0], filesize);

    CURL* curl = curl_easy_init();
    if (!curl) {
        std::cerr << "Failed to initialize curl" << std::endl;
        return 1;
    }
    struct curl_slist* headers = nullptr;
    std::string filename_header = "X-Filename: " + file_path.substr(file_path.find_last_of("/\\") + 1);
    headers = curl_slist_append(headers, filename_header.c_str());
    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, filedata.c_str());
    curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE, filesize);
    curl_easy_setopt(curl, CURLOPT_HTTPAUTH, CURLAUTH_BASIC);
    std::string userpwd = username + ":" + password;
    curl_easy_setopt(curl, CURLOPT_USERPWD, userpwd.c_str());
    
    // Set up progress monitoring
    curl_easy_setopt(curl, CURLOPT_XFERINFOFUNCTION, progress_callback);
    curl_easy_setopt(curl, CURLOPT_XFERINFODATA, nullptr);
    curl_easy_setopt(curl, CURLOPT_NOPROGRESS, 0L);
    
    // Set timeout
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 300L); // 5 minutes
    
    std::cout << "Starting upload of " << file_path << " (" << filesize << " bytes)" << std::endl;
    auto start = std::chrono::high_resolution_clock::now();
    
    // Perform the upload    // Perform the upload
    CURLcode res = curl_easy_perform(curl);
    
    // Calculate elapsed time
    auto end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> elapsed = end - start;
    
    std::cout << std::endl;
    
    if (res != CURLE_OK) {
        std::cerr << "Upload failed: " << curl_easy_strerror(res) << std::endl;
    } else {
        // Get server response
        long http_code = 0;
        curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_code);
        
        if (http_code == 200) {
            double upload_speed;
            curl_easy_getinfo(curl, CURLINFO_SPEED_UPLOAD, &upload_speed);
            double total_time;
            curl_easy_getinfo(curl, CURLINFO_TOTAL_TIME, &total_time);
            
            std::cout << "File uploaded successfully in " << std::fixed << std::setprecision(2) << elapsed.count() << " seconds";
            std::cout << " (" << std::fixed << std::setprecision(2) << (filesize / 1024.0 / 1024.0) / elapsed.count() << " MB/s)" << std::endl;
        } else {
            std::cerr << "Server returned code " << http_code << std::endl;
        }
    }
    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);
    return 0;
}
