import string
allAlphabets = string.ascii_lowercase

previousFirstVal = 0
previousSecondVal = 1
json = {}
json['a'] = 0
json['b'] = 1
for single in allAlphabets[2:]:
    newVal = (previousSecondVal + previousFirstVal)
    json[str(single)] = newVal
    previousFirstVal = previousSecondVal
    previousSecondVal = newVal

userInput = input('Enter A Word ')
filteredInput = ''.join(e for e in userInput if e.isalnum())
finalOutput = 0
for character in filteredInput.lower():
    finalOutput += json[character]
print(finalOutput)