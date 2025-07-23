import nltk
from nltk.corpus import cmudict, words
import json
import re

# Initialize NLTK's CMUdict and 'words' corpus
# Ensure you've downloaded them via nltk.download('cmudict') and nltk.download('words')
d = cmudict.dict()
english_words = set(w.lower() for w in words.words()) # Convert to lowercase set for fast lookup

def get_pronunciation(word):
    """
    Returns the CMUdict pronunciation for a word.
    Handles capitalization by checking lowercase.
    Returns None if word not found.
    """
    word_lower = word.lower()
    if word_lower in d:
        # CMUdict can have multiple pronunciations; we'll take the first one for simplicity.
        return d[word_lower][0]
    return None

def filter_words_by_length(min_len, max_len):
    """
    Filters the English word list to contain words within a specified length range,
    and ensures they have a pronunciation entry in CMUdict.
    """
    filtered_words = set()
    for word in english_words:
        # Filter by length and ensure it's alphabetic
        if min_len <= len(word) <= max_len and word.isalpha():
            # Check if pronunciation exists (crucial for homophone/rhyme generation)
            if get_pronunciation(word):
                filtered_words.add(word)
    return sorted(list(filtered_words)) # Return sorted list for consistent processing

def find_homophones(word_list):
    """
    Finds homophones for each word in the given list.
    A homophone has the same pronunciation but different spelling.
    """
    homophones_map = {}
    pronunciation_to_words = {} # Map pronunciation string to list of words

    # First, build a map from pronunciation to words
    for word in word_list:
        pron = get_pronunciation(word)
        if pron:
            # Convert pronunciation list to a tuple for hashability
            pron_tuple = tuple(pron)
            if pron_tuple not in pronunciation_to_words:
                pronunciation_to_words[pron_tuple] = []
            pronunciation_to_words[pron_tuple].append(word)

    # Now, identify homophones
    for word in word_list:
        pron = get_pronunciation(word)
        if pron:
            pron_tuple = tuple(pron)
            potential_homophones = pronunciation_to_words.get(pron_tuple, [])
            actual_homophones = [h for h in potential_homophones if h != word]
            if actual_homophones:
                homophones_map[word] = sorted(actual_homophones)
    return homophones_map

def find_rhyming_words(word_list):
    """
    Finds rhyming words for each word in the given list.
    Rhymes share the last stressed vowel and all subsequent sounds.
    """
    rhymes_map = {}
    rhyme_group_to_words = {} # Map rhyme suffix to list of words

    for word in word_list:
        pron = get_pronunciation(word)
        if pron:
            # Find the last stressed vowel (indicated by a digit, usually 1 or 2)
            # and take all sounds from there to the end.
            rhyme_suffix_parts = []
            found_stress = False
            for i in reversed(range(len(pron))):
                phone = pron[i]
                rhyme_suffix_parts.insert(0, phone)
                if re.search(r'\d', phone): # Check if the phone contains a stress marker (e.g., 'AY1')
                    found_stress = True
                    break
            
            if found_stress:
                rhyme_suffix = tuple(rhyme_suffix_parts)
                if rhyme_suffix not in rhyme_group_to_words:
                    rhyme_group_to_words[rhyme_suffix] = []
                rhyme_group_to_words[rhyme_suffix].append(word)

    # Now, identify rhymes
    for word in word_list:
        pron = get_pronunciation(word)
        if pron:
            rhyme_suffix_parts = []
            found_stress = False
            for i in reversed(range(len(pron))):
                phone = pron[i]
                rhyme_suffix_parts.insert(0, phone)
                if re.search(r'\d', phone):
                    found_stress = True
                    break

            if found_stress:
                rhyme_suffix = tuple(rhyme_suffix_parts)
                potential_rhymes = rhyme_group_to_words.get(rhyme_suffix, [])
                actual_rhymes = [r for r in potential_rhymes if r != word] # Exclude the word itself
                if actual_rhymes:
                    rhymes_map[word] = sorted(actual_rhymes)
    return rhymes_map

def find_one_letter_additions(word_list, all_valid_words):
    """
    Finds words that can be created by adding one letter to a given word.
    """
    additions_map = {}
    alphabet = "abcdefghijklmnopqrstuvwxyz"

    # Convert the list of all valid words to a set for efficient lookup
    all_valid_words_set = set(all_valid_words) 

    for word in word_list:
        possible_additions = []
        # Try adding at the beginning
        for char in alphabet:
            new_word = char + word
            if new_word in all_valid_words_set and new_word != word:
                possible_additions.append(new_word)
        
        # Try adding in between existing letters
        for i in range(len(word)):
            for char in alphabet:
                new_word = word[:i+1] + char + word[i+1:]
                if new_word in all_valid_words_set and new_word != word:
                    possible_additions.append(new_word)
        
        # Try adding at the end
        for char in alphabet:
            new_word = word + char
            if new_word in all_valid_words_set and new_word != word:
                possible_additions.append(new_word)
        
        if possible_additions:
            additions_map[word] = sorted(list(set(possible_additions))) # Use set to remove duplicates, then sort
    return additions_map

def main():
    print("Step 1: Data Acquisition & Preprocessing initiated.")

    min_len = 3
    max_len = 7
    print(f"Filtering words between {min_len} and {max_len} letters and with CMUdict pronunciations...")
    filtered_words = filter_words_by_length(min_len, max_len)
    print(f"Found {len(filtered_words)} valid words.")

    print("Finding homophones (this might take a while for large lists)...")
    homophones_data = find_homophones(filtered_words)
    print(f"Found homophones for {len(homophones_data)} words.")

    print("Finding rhyming words (this might take a while for large lists)...")
    rhyming_data = find_rhyming_words(filtered_words)
    print(f"Found rhyming words for {len(rhyming_data)} words.")

    print("Finding one-letter additions (this might take a while for large lists)...")
    additions_data = find_one_letter_additions(filtered_words, filtered_words) # Pass filtered_words as all_valid_words
    print(f"Found additions for {len(additions_data)} words.")

    # Save to JSON files for inspection and later loading into Redis
    with open('filtered_words.json', 'w') as f:
        json.dump(filtered_words, f, indent=4)
    print("Saved filtered_words.json")

    with open('homophones.json', 'w') as f:
        json.dump(homophones_data, f, indent=4)
    print("Saved homophones.json")

    with open('rhymes.json', 'w') as f:
        json.dump(rhyming_data, f, indent=4)
    print("Saved rhymes.json")

    with open('additions.json', 'w') as f:
        json.dump(additions_data, f, indent=4)
    print("Saved additions.json")

    print("Data preprocessing complete!")

if __name__ == "__main__":
    main()
