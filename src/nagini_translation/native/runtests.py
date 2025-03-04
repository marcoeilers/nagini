import os
#iterate over files contained in ./tests directory and starting with test_
os.chdir("./src/nagini_translation/native/")  # Change to a new directory
for filename in os.listdir('./tests'):
    print(filename)
    if filename.startswith("test_"):
        pass