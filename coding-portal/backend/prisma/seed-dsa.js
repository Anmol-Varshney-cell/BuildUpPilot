import { PrismaClient, Difficulty } from '@prisma/client';
const prisma = new PrismaClient();
const dsaProblems = [
    // Easy Problems (10)
    {
        slug: 'two-sum',
        title: 'Two Sum',
        difficulty: Difficulty.EASY,
        tags: ['arrays', 'hashing'],
        supportedLanguages: ['PYTHON', 'JAVASCRIPT', 'JAVA', 'CPP'],
        statement: `Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.

You may assume that each input would have exactly one solution, and you may not use the same element twice.

You can return the answer in any order.`,
        inputFormat: `First line contains n (number of elements in array).
Second line contains n space-separated integers.
Third line contains the target integer.`,
        outputFormat: `Print two space-separated indices (0-based) of the numbers that add up to target.`,
        constraints: `2 <= nums.length <= 10^4
-10^9 <= nums[i] <= 10^9
-10^9 <= target <= 10^9`,
        sampleInput: `4
2 7 11 15
9`,
        sampleOutput: `0 1`,
        explanation: `Use a hash map to store complement values and their indices. For each number, check if its complement exists in the map.`,
        starterCodes: {
            PYTHON: `def two_sum(nums, target):
    # Your code here
    pass`,
            JAVASCRIPT: `function twoSum(nums, target) {
    // Your code here
}`,
            JAVA: `class Solution {
    public int[] twoSum(int[] nums, int target) {
        // Your code here
    }
}`,
            CPP: `class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        // Your code here
    }
};`
        },
        timeLimitMs: 1000,
        memoryLimitMb: 128
    },
    {
        slug: 'valid-parentheses',
        title: 'Valid Parentheses',
        difficulty: Difficulty.EASY,
        tags: ['stack', 'string'],
        supportedLanguages: ['PYTHON', 'JAVASCRIPT', 'JAVA', 'CPP'],
        statement: `Given a string s containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid.

An input string is valid if:

Open brackets must be closed by the same type of brackets.
Open brackets must be closed in the correct order.`,
        inputFormat: `A single string s containing only '(', ')', '{', '}', '[' and ']'.`,
        outputFormat: `Print "true" if the string is valid, otherwise print "false".`,
        constraints: `1 <= s.length <= 10^4`,
        sampleInput: `()`,
        sampleOutput: `true`,
        explanation: `Use a stack to keep track of opening brackets. When you encounter a closing bracket, check if it matches the top of the stack.`,
        starterCodes: {
            PYTHON: `def is_valid(s):
    # Your code here
    pass`,
            JAVASCRIPT: `function isValid(s) {
    // Your code here
}`,
            JAVA: `class Solution {
    public boolean isValid(String s) {
        // Your code here
    }
}`,
            CPP: `class Solution {
public:
    bool isValid(string s) {
        // Your code here
    }
};`
        },
        timeLimitMs: 1000,
        memoryLimitMb: 128
    },
    {
        slug: 'palindrome-number',
        title: 'Palindrome Number',
        difficulty: Difficulty.EASY,
        tags: ['math', 'string'],
        supportedLanguages: ['PYTHON', 'JAVASCRIPT', 'JAVA', 'CPP'],
        statement: `Given an integer x, return true if x is a palindrome, and false otherwise.`,
        inputFormat: `A single integer x.`,
        outputFormat: `Print "true" if x is a palindrome, otherwise print "false".`,
        constraints: `-2^31 <= x <= 2^31 - 1`,
        sampleInput: `121`,
        sampleOutput: `true`,
        explanation: `A number is a palindrome if it reads the same forwards and backwards. You can reverse the number and compare.`,
        starterCodes: {
            PYTHON: `def is_palindrome(x):
    # Your code here
    pass`,
            JAVASCRIPT: `function isPalindrome(x) {
    // Your code here
}`,
            JAVA: `class Solution {
    public boolean isPalindrome(int x) {
        // Your code here
    }
}`,
            CPP: `class Solution {
public:
    bool isPalindrome(int x) {
        // Your code here
    }
};`
        },
        timeLimitMs: 1000,
        memoryLimitMb: 128
    },
    {
        slug: 'fizz-buzz',
        title: 'Fizz Buzz',
        difficulty: Difficulty.EASY,
        tags: ['array', 'simulation'],
        supportedLanguages: ['PYTHON', 'JAVASCRIPT', 'JAVA', 'CPP'],
        statement: `Given an integer n, return a string array answer (1-indexed) where:

answer[i] == "FizzBuzz" if i is divisible by 3 and 5.
answer[i] == "Fizz" if i is divisible by 3.
answer[i] == "Buzz" if i is divisible by 5.
answer[i] == i (as a string) if none of the above conditions are true.`,
        inputFormat: `A single integer n.`,
        outputFormat: `Print space-separated values from answer[1] to answer[n].`,
        constraints: `1 <= n <= 10^4`,
        sampleInput: `3`,
        sampleOutput: `1 2 Fizz`,
        explanation: `Iterate from 1 to n, checking divisibility conditions for each number.`,
        starterCodes: {
            PYTHON: `def fizz_buzz(n):
    # Your code here
    pass`,
            JAVASCRIPT: `function fizzBuzz(n) {
    // Your code here
}`,
            JAVA: `class Solution {
    public List<String> fizzBuzz(int n) {
        // Your code here
    }
}`,
            CPP: `class Solution {
public:
    vector<string> fizzBuzz(int n) {
        // Your code here
    }
};`
        },
        timeLimitMs: 1000,
        memoryLimitMb: 128
    },
    {
        slug: 'missing-number',
        title: 'Missing Number',
        difficulty: Difficulty.EASY,
        tags: ['array', 'math'],
        supportedLanguages: ['PYTHON', 'JAVASCRIPT', 'JAVA', 'CPP'],
        statement: `Given an array nums containing n distinct numbers in the range [0, n], return the only number in the range that is missing from the array.`,
        inputFormat: `First line contains n.
Second line contains n space-separated distinct integers.`,
        outputFormat: `Print the missing number.`,
        constraints: `1 <= nums.length <= 10^4`,
        sampleInput: `3
0 1 3`,
        sampleOutput: `2`,
        explanation: `The sum of numbers from 0 to n is n*(n+1)/2. Subtract the sum of the array to find the missing number.`,
        starterCodes: {
            PYTHON: `def missing_number(nums):
    # Your code here
    pass`,
            JAVASCRIPT: `function missingNumber(nums) {
    // Your code here
}`,
            JAVA: `class Solution {
    public int missingNumber(int[] nums) {
        // Your code here
    }
}`,
            CPP: `class Solution {
public:
    int missingNumber(vector<int>& nums) {
        // Your code here
    }
};`
        },
        timeLimitMs: 1000,
        memoryLimitMb: 128
    },
    {
        slug: 'reverse-string',
        title: 'Reverse String',
        difficulty: Difficulty.EASY,
        tags: ['string', 'two-pointers'],
        supportedLanguages: ['PYTHON', 'JAVASCRIPT', 'JAVA', 'CPP'],
        statement: `Write a function that reverses a string. The input string is given read from left to right, and the output string should be read from right to left.`,
        inputFormat: `A single string s.`,
        outputFormat: `Print the reversed string.`,
        constraints: `0 <= s.length <= 10^4`,
        sampleInput: `hello`,
        sampleOutput: `olleh`,
        explanation: `Use two pointers approach - one at start, one at end, swapping characters until they meet in the middle.`,
        starterCodes: {
            PYTHON: `def reverse_string(s):
    # Your code here
    pass`,
            JAVASCRIPT: `function reverseString(s) {
    // Your code here
}`,
            JAVA: `class Solution {
    public String reverseString(String s) {
        // Your code here
    }
}`,
            CPP: `class Solution {
public:
    string reverseString(string s) {
        // Your code here
    }
};`
        },
        timeLimitMs: 1000,
        memoryLimitMb: 128
    },
    {
        slug: 'contains-duplicate',
        title: 'Contains Duplicate',
        difficulty: Difficulty.EASY,
        tags: ['array', 'hashing'],
        supportedLanguages: ['PYTHON', 'JAVASCRIPT', 'JAVA', 'CPP'],
        statement: `Given an integer array nums, return true if any value appears at least twice in the array, and return false if every element is distinct.`,
        inputFormat: `First line contains n.
Second line contains n space-separated integers.`,
        outputFormat: `Print "true" if duplicate exists, otherwise print "false".`,
        constraints: `1 <= nums.length <= 10^4`,
        sampleInput: `3
1 2 3 1`,
        sampleOutput: `true`,
        explanation: `Use a hash set to track seen numbers. If you encounter a number already in the set, return true.`,
        starterCodes: {
            PYTHON: `def contains_duplicate(nums):
    # Your code here
    pass`,
            JAVASCRIPT: `function containsDuplicate(nums) {
    // Your code here
}`,
            JAVA: `class Solution {
    public boolean containsDuplicate(int[] nums) {
        // Your code here
    }
}`,
            CPP: `class Solution {
public:
    bool containsDuplicate(vector<int>& nums) {
        // Your code here
    }
};`
        },
        timeLimitMs: 1000,
        memoryLimitMb: 128
    },
    {
        slug: 'max-subarray',
        title: 'Maximum Subarray',
        difficulty: Difficulty.EASY,
        tags: ['array', 'dynamic-programming'],
        supportedLanguages: ['PYTHON', 'JAVASCRIPT', 'JAVA', 'CPP'],
        statement: `Given an integer array nums, find the contiguous subarray (containing at least one number) which has the largest sum and return its sum.`,
        inputFormat: `First line contains n.
Second line contains n space-separated integers.`,
        outputFormat: `Print the maximum subarray sum.`,
        constraints: `1 <= nums.length <= 10^4`,
        sampleInput: `5
-2 1 -3 4 -1 2 1 -5 4`,
        sampleOutput: `6`,
        explanation: `Use Kadane's algorithm - keep track of current sum and maximum sum seen so far.`,
        starterCodes: {
            PYTHON: `def max_subarray(nums):
    # Your code here
    pass`,
            JAVASCRIPT: `function maxSubarray(nums) {
    // Your code here
}`,
            JAVA: `class Solution {
    public int maxSubArray(int[] nums) {
        // Your code here
    }
}`,
            CPP: `class Solution {
public:
    int maxSubArray(vector<int>& nums) {
        // Your code here
    }
};`
        },
        timeLimitMs: 1000,
        memoryLimitMb: 128
    },
    {
        slug: 'climbing-stairs',
        title: 'Climbing Stairs',
        difficulty: Difficulty.EASY,
        tags: ['dynamic-programming', 'math'],
        supportedLanguages: ['PYTHON', 'JAVASCRIPT', 'JAVA', 'CPP'],
        statement: `You are climbing a staircase. It takes n steps to reach the top.

Each time you can either climb 1 or 2 steps. In how many distinct ways can you climb to the top?`,
        inputFormat: `A single integer n.`,
        outputFormat: `Print the number of distinct ways to climb to the top.`,
        constraints: `1 <= n <= 45`,
        sampleInput: `3`,
        sampleOutput: `3`,
        explanation: `This is a Fibonacci sequence problem. ways(n) = ways(n-1) + ways(n-2) with base cases ways(1) = 1, ways(2) = 2.`,
        starterCodes: {
            PYTHON: `def climb_stairs(n):
    # Your code here
    pass`,
            JAVASCRIPT: `function climbStairs(n) {
    // Your code here
}`,
            JAVA: `class Solution {
    public int climbStairs(int n) {
        // Your code here
    }
}`,
            CPP: `class Solution {
public:
    int climbStairs(int n) {
        // Your code here
    }
};`
        },
        timeLimitMs: 1000,
        memoryLimitMb: 128
    },
    {
        slug: 'best-time-to-buy',
        title: 'Best Time to Buy and Sell Stock',
        difficulty: Difficulty.EASY,
        tags: ['array', 'greedy'],
        supportedLanguages: ['PYTHON', 'JAVASCRIPT', 'JAVA', 'CPP'],
        statement: `You are given an array prices where prices[i] is the price of a given stock on the ith day.

Find the maximum profit you can achieve. You may complete at most one transaction (i.e., buy one and sell one share of the stock).`,
        inputFormat: `First line contains n.
Second line contains n space-separated integers.`,
        outputFormat: `Print the maximum profit.`,
        constraints: `1 <= prices.length <= 10^4`,
        sampleInput: `7
7 1 5 3 6 4`,
        sampleOutput: `5`,
        explanation: `Track the minimum price seen so far and calculate profit for each day. The maximum profit is the answer.`,
        starterCodes: {
            PYTHON: `def max_profit(prices):
    # Your code here
    pass`,
            JAVASCRIPT: `function maxProfit(prices) {
    // Your code here
}`,
            JAVA: `class Solution {
    public int maxProfit(int[] prices) {
        // Your code here
    }
}`,
            CPP: `class Solution {
public:
    int maxProfit(vector<int>& prices) {
        // Your code here
    }
};`
        },
        timeLimitMs: 1000,
        memoryLimitMb: 128
    },
    {
        slug: 'valid-anagram',
        title: 'Valid Anagram',
        difficulty: Difficulty.EASY,
        tags: ['string', 'hashing'],
        supportedLanguages: ['PYTHON', 'JAVASCRIPT', 'JAVA', 'CPP'],
        statement: `Given two strings s and t, return true if t is an anagram of s, and false otherwise.

An anagram is a word or phrase formed by rearranging the letters of a different word or phrase, typically using all the original letters exactly once.`,
        inputFormat: `Two lines:
First line: string s
Second line: string t`,
        outputFormat: `Print "true" if t is an anagram of s, otherwise print "false".`,
        constraints: `1 <= s.length, t.length <= 5 * 10^4`,
        sampleInput: `anagram
nagaram`,
        sampleOutput: `true`,
        explanation: `Two strings are anagrams if they have the same character frequencies. Use a frequency array or hash map.`,
        starterCodes: {
            PYTHON: `def is_anagram(s, t):
    # Your code here
    pass`,
            JAVASCRIPT: `function isAnagram(s, t) {
    // Your code here
}`,
            JAVA: `class Solution {
    public boolean isAnagram(String s, String t) {
        // Your code here
    }
}`,
            CPP: `class Solution {
public:
    bool isAnagram(string s, string t) {
        // Your code here
    }
};`
        },
        timeLimitMs: 1000,
        memoryLimitMb: 128
    },
    {
        slug: 'binary-search',
        title: 'Binary Search',
        difficulty: Difficulty.EASY,
        tags: ['array', 'binary-search'],
        supportedLanguages: ['PYTHON', 'JAVASCRIPT', 'JAVA', 'CPP'],
        statement: `Given an array of integers nums which is sorted in ascending order, and an integer target, write a function to search target in nums.

If target exists, then return its index. Otherwise, return -1.

You must write an algorithm with O(log n) runtime complexity.`,
        inputFormat: `First line contains n.
Second line contains n space-separated integers in sorted order.
Third line contains target integer.`,
        outputFormat: `Print the index of target if found, otherwise print -1.`,
        constraints: `1 <= nums.length <= 10^4`,
        sampleInput: `4
-1 0 3 5 9 12`,
        sampleOutput: `4`,
        explanation: `Use binary search: compare target with middle element and adjust search range accordingly.`,
        starterCodes: {
            PYTHON: `def binary_search(nums, target):
    # Your code here
    pass`,
            JAVASCRIPT: `function binarySearch(nums, target) {
    // Your code here
}`,
            JAVA: `class Solution {
    public int search(int[] nums, int target) {
        // Your code here
    }
}`,
            CPP: `class Solution {
public:
    int search(vector<int>& nums, int target) {
        // Your code here
    }
};`
        },
        timeLimitMs: 1000,
        memoryLimitMb: 128
    },
    // Medium Problems (10)
    {
        slug: 'longest-substring-without-repeating',
        title: 'Longest Substring Without Repeating Characters',
        difficulty: Difficulty.MEDIUM,
        tags: ['string', 'sliding-window'],
        supportedLanguages: ['PYTHON', 'JAVASCRIPT', 'JAVA', 'CPP'],
        statement: `Given a string s, find the length of the longest substring without repeating characters.`,
        inputFormat: `A single string s.`,
        outputFormat: `Print the length of the longest substring without repeating characters.`,
        constraints: `0 <= s.length <= 5 * 10^4`,
        sampleInput: `abcabcbb`,
        sampleOutput: `3`,
        explanation: `Use sliding window with a hash set to track characters in current window. Expand window while no duplicates, shrink when duplicate found.`,
        starterCodes: {
            PYTHON: `def length_of_longest_substring(s):
    # Your code here
    pass`,
            JAVASCRIPT: `function lengthOfLongestSubstring(s) {
    // Your code here
}`,
            JAVA: `class Solution {
    public int lengthOfLongestSubstring(String s) {
        // Your code here
    }
}`,
            CPP: `class Solution {
public:
    int lengthOfLongestSubstring(string s) {
        // Your code here
    }
};`
        },
        timeLimitMs: 1500,
        memoryLimitMb: 256
    },
    {
        slug: 'add-two-numbers',
        title: 'Add Two Numbers',
        difficulty: Difficulty.MEDIUM,
        tags: ['linked-list', 'math'],
        supportedLanguages: ['PYTHON', 'JAVASCRIPT', 'JAVA', 'CPP'],
        statement: `You are given two non-empty linked lists representing two non-negative integers. The digits are stored in reverse order, and each of their nodes contains a single digit.

Add the two numbers and return the sum as a linked list.`,
        inputFormat: `First line: m (number of nodes in first list)
Second line: m space-separated digits (reverse order)
Third line: n (number of nodes in second list)
Fourth line: n space-separated digits (reverse order)`,
        outputFormat: `Print the sum as space-separated digits in reverse order.`,
        constraints: `1 <= m, n <= 100`,
        sampleInput: `2
2 4
3
5 6`,
        sampleOutput: `7 0 8`,
        explanation: `Traverse both lists simultaneously, adding digits and handling carry. Build result list in reverse order.`,
        starterCodes: {
            PYTHON: `def add_two_numbers(l1, l2):
    # Your code here
    pass`,
            JAVASCRIPT: `function addTwoNumbers(l1, l2) {
    // Your code here
}`,
            JAVA: `class Solution {
    public ListNode addTwoNumbers(ListNode l1, ListNode l2) {
        // Your code here
    }
}`,
            CPP: `class Solution {
public:
    ListNode* addTwoNumbers(ListNode* l1, ListNode* l2) {
        // Your code here
    }
};`
        },
        timeLimitMs: 1500,
        memoryLimitMb: 256
    },
    {
        slug: 'longest-palindromic-substring',
        title: 'Longest Palindromic Substring',
        difficulty: Difficulty.MEDIUM,
        tags: ['string', 'dynamic-programming'],
        supportedLanguages: ['PYTHON', 'JAVASCRIPT', 'JAVA', 'CPP'],
        statement: `Given a string s, return the longest palindromic substring in s.`,
        inputFormat: `A single string s.`,
        outputFormat: `Print the longest palindromic substring.`,
        constraints: `1 <= s.length <= 1000`,
        sampleInput: `babad`,
        sampleOutput: `bab`,
        explanation: `Use DP or expand around center approach. For each center, expand outward while characters match.`,
        starterCodes: {
            PYTHON: `def longest_palindrome(s):
    # Your code here
    pass`,
            JAVASCRIPT: `function longestPalindrome(s) {
    // Your code here
}`,
            JAVA: `class Solution {
    public String longestPalindrome(String s) {
        // Your code here
    }
}`,
            CPP: `class Solution {
public:
    string longestPalindrome(string s) {
        // Your code here
    }
};`
        },
        timeLimitMs: 1500,
        memoryLimitMb: 256
    },
    {
        slug: 'container-with-most-water',
        title: 'Container With Most Water',
        difficulty: Difficulty.MEDIUM,
        tags: ['array', 'two-pointers'],
        supportedLanguages: ['PYTHON', 'JAVASCRIPT', 'JAVA', 'CPP'],
        statement: `You are given an array height where height[i] represents the height of a vertical line drawn at coordinate i.

Find two lines that together with the x-axis form a container, such that the container contains the most water.`,
        inputFormat: `First line contains n.
Second line contains n space-separated integers.`,
        outputFormat: `Print the maximum amount of water the container can store.`,
        constraints: `2 <= height.length <= 10^4`,
        sampleInput: `9
1 8 6 2 5 4 8 3 7`,
        sampleOutput: `49`,
        explanation: `Use two-pointer approach: left at start, right at end. Move pointers inward tracking max area.`,
        starterCodes: {
            PYTHON: `def max_area(height):
    # Your code here
    pass`,
            JAVASCRIPT: `function maxArea(height) {
    // Your code here
}`,
            JAVA: `class Solution {
    public int maxArea(int[] height) {
        // Your code here
    }
}`,
            CPP: `class Solution {
public:
    int maxArea(vector<int>& height) {
        // Your code here
    }
};`
        },
        timeLimitMs: 1500,
        memoryLimitMb: 256
    },
    {
        slug: '3sum',
        title: '3Sum',
        difficulty: Difficulty.MEDIUM,
        tags: ['array', 'two-pointers'],
        supportedLanguages: ['PYTHON', 'JAVASCRIPT', 'JAVA', 'CPP'],
        statement: `Given an integer array nums, return all the triplets [nums[i], nums[j], nums[k]] such that i != j, i != k, and j != k, and nums[i] + nums[j] + nums[k] == 0.

Notice that the solution set must not contain duplicate triplets.`,
        inputFormat: `First line contains n.
Second line contains n space-separated integers.`,
        outputFormat: `Print each triplet on a new line as space-separated values in sorted order.`,
        constraints: `0 <= nums.length <= 3000`,
        sampleInput: `6
-1 0 1 2 -1 -4`,
        sampleOutput: `-1 -1 2
-1 0 1 2`,
        explanation: `Sort array, then use two-pointer approach for each element. Skip duplicates to avoid duplicate triplets.`,
        starterCodes: {
            PYTHON: `def three_sum(nums):
    # Your code here
    pass`,
            JAVASCRIPT: `function threeSum(nums) {
    // Your code here
}`,
            JAVA: `class Solution {
    public List<List<Integer>> threeSum(int[] nums) {
        // Your code here
    }
}`,
            CPP: `class Solution {
public:
    vector<vector<int>> threeSum(vector<int>& nums) {
        // Your code here
    }
};`
        },
        timeLimitMs: 2000,
        memoryLimitMb: 256
    },
    {
        slug: 'group-anagrams',
        title: 'Group Anagrams',
        difficulty: Difficulty.MEDIUM,
        tags: ['string', 'hashing'],
        supportedLanguages: ['PYTHON', 'JAVASCRIPT', 'JAVA', 'CPP'],
        statement: `Given an array of strings strs, group the anagrams together. You can return the answer in any order.

An anagram is a word or phrase formed by rearranging the letters of a different word or phrase.`,
        inputFormat: `First line contains n.
Next n lines contain strings.`,
        outputFormat: `Print each group of anagrams on a new line, with strings in each group space-separated.`,
        constraints: `1 <= strs.length <= 10^4`,
        sampleInput: `4
eat
tea
tan
ate`,
        sampleOutput: `eat tea ate`,
        explanation: `Two strings are anagrams if sorted versions are equal. Use sorted string as key in hash map.`,
        starterCodes: {
            PYTHON: `def group_anagrams(strs):
    # Your code here
    pass`,
            JAVASCRIPT: `function groupAnagrams(strs) {
    // Your code here
}`,
            JAVA: `class Solution {
    public List<List<String>> groupAnagrams(String[] strs) {
        // Your code here
    }
}`,
            CPP: `class Solution {
public:
    vector<vector<string>> groupAnagrams(vector<string>& strs) {
        // Your code here
    }
};`
        },
        timeLimitMs: 2000,
        memoryLimitMb: 256
    },
    {
        slug: 'rotate-image',
        title: 'Rotate Image',
        difficulty: Difficulty.MEDIUM,
        tags: ['array', 'matrix'],
        supportedLanguages: ['PYTHON', 'JAVASCRIPT', 'JAVA', 'CPP'],
        statement: `You are given an n x n 2D matrix representing an image.

Rotate the image by 90 degrees (clockwise).`,
        inputFormat: `First line contains n.
Next n lines contain n space-separated integers each.`,
        outputFormat: `Print the rotated matrix, each row on a new line with space-separated values.`,
        constraints: `1 <= n <= 20`,
        sampleInput: `3
1 2 3
4 5 6
7 8 9`,
        sampleOutput: `7 4 1
8 5 2
9 6 3`,
        explanation: `Transpose matrix, then reverse each row. Or rotate layer by layer from outer to inner.`,
        starterCodes: {
            PYTHON: `def rotate(matrix):
    # Your code here
    pass`,
            JAVASCRIPT: `function rotate(matrix) {
    // Your code here
}`,
            JAVA: `class Solution {
    public void rotate(int[][] matrix) {
        // Your code here
    }
}`,
            CPP: `class Solution {
public:
    void rotate(vector<vector<int>>& matrix) {
        // Your code here
    }
};`
        },
        timeLimitMs: 2000,
        memoryLimitMb: 256
    },
    {
        slug: 'spiral-matrix',
        title: 'Spiral Matrix',
        difficulty: Difficulty.MEDIUM,
        tags: ['array', 'matrix'],
        supportedLanguages: ['PYTHON', 'JAVASCRIPT', 'JAVA', 'CPP'],
        statement: `Given an m x n matrix, return all elements of the matrix in spiral order.`,
        inputFormat: `First line contains m n.
Next m lines contain n space-separated integers each.`,
        outputFormat: `Print matrix elements in spiral order as space-separated values.`,
        constraints: `1 <= m, n <= 10`,
        sampleInput: `3 4
1 2 3 4
5 6 7 8
9 10 11 12`,
        sampleOutput: `1 2 3 4 8 12 11 10 9 5 6 7`,
        explanation: `Use four boundaries (top, bottom, left, right) and traverse in order: right, down, left, up, shrinking boundaries.`,
        starterCodes: {
            PYTHON: `def spiral_order(matrix):
    # Your code here
    pass`,
            JAVASCRIPT: `function spiralOrder(matrix) {
    // Your code here
}`,
            JAVA: `class Solution {
    public List<Integer> spiralOrder(int[][] matrix) {
        // Your code here
    }
}`,
            CPP: `class Solution {
public:
    vector<int> spiralOrder(vector<vector<int>>& matrix) {
        // Your code here
    }
};`
        },
        timeLimitMs: 2000,
        memoryLimitMb: 256
    },
    // Hard Problems (10)
    {
        slug: 'merge-k-sorted-lists',
        title: 'Merge K Sorted Lists',
        difficulty: Difficulty.HARD,
        tags: ['linked-list', 'divide-and-conquer'],
        supportedLanguages: ['PYTHON', 'JAVASCRIPT', 'JAVA', 'CPP'],
        statement: `You are given an array of k linked-lists lists, each linked-list is sorted in ascending order.

Merge all the linked-lists into one sorted linked-list and return it.`,
        inputFormat: `First line contains k.
Next k lines each contain: m (number of nodes) followed by m space-separated values.`,
        outputFormat: `Print the merged list as space-separated values.`,
        constraints: `1 <= k <= 10^4`,
        sampleInput: `3
1 4 5
1 3 4
2 6`,
        sampleOutput: `1 1 2 3 4 5 6`,
        explanation: `Use min-heap to always pick smallest head element. Or use divide and conquer merging pairs repeatedly.`,
        starterCodes: {
            PYTHON: `def merge_k_lists(lists):
    # Your code here
    pass`,
            JAVASCRIPT: `function mergeKLists(lists) {
    // Your code here
}`,
            JAVA: `class Solution {
    public ListNode mergeKLists(ListNode[] lists) {
        // Your code here
    }
}`,
            CPP: `class Solution {
public:
    ListNode* mergeKLists(vector<ListNode*>& lists) {
        // Your code here
    }
};`
        },
        timeLimitMs: 3000,
        memoryLimitMb: 512
    },
    {
        slug: 'regular-expression-matching',
        title: 'Regular Expression Matching',
        difficulty: Difficulty.HARD,
        tags: ['string', 'dynamic-programming'],
        supportedLanguages: ['PYTHON', 'JAVASCRIPT', 'JAVA', 'CPP'],
        statement: `Given an input string s and a pattern p, implement regular expression matching with support for '.' and '*' where:

'.' Matches any single character
'*' Matches zero or more of the preceding element`,
        inputFormat: `Two lines:
First line: string s
Second line: pattern p`,
        outputFormat: `Print "true" if pattern matches string, otherwise print "false".`,
        constraints: `0 <= s.length <= 20
0 <= p.length <= 30`,
        sampleInput: `aab
c*a*b`,
        sampleOutput: `true`,
        explanation: `Use DP: dp[i][j] represents if s[i:] matches p[j:]. Handle '.' and '*' cases accordingly.`,
        starterCodes: {
            PYTHON: `def is_match(s, p):
    # Your code here
    pass`,
            JAVASCRIPT: `function isMatch(s, p) {
    // Your code here
}`,
            JAVA: `class Solution {
    public boolean isMatch(String s, String p) {
        // Your code here
    }
}`,
            CPP: `class Solution {
public:
    bool isMatch(string s, string p) {
        // Your code here
    }
};`
        },
        timeLimitMs: 3000,
        memoryLimitMb: 512
    },
    {
        slug: 'median-of-two-streams',
        title: 'Median of Two Data Streams',
        difficulty: Difficulty.HARD,
        tags: ['heap', 'design'],
        supportedLanguages: ['PYTHON', 'JAVASCRIPT', 'JAVA', 'CPP'],
        statement: `The median is the middle value in an ordered integer list. If the size of the list is even, there is no middle value and the median is the mean of the two middle values.

Implement the MedianFinder class that supports:
- addNum(int num): Add integer number from the data stream to the data structure.
- findMedian(): Return the median of all elements so far.`,
        inputFormat: `Commands:
- "add x": Add integer x to the stream
- "median": Find and print the median
- "end": Terminate`,
        outputFormat: `For each "median" command, print the median value.`,
        constraints: `Up to 10^5 operations`,
        sampleInput: `add 1
add 2
median
add 3
median`,
        sampleOutput: `1.5
2`,
        explanation: `Use two heaps: max-heap for lower half, min-heap for upper half. Maintain size balance.`,
        starterCodes: {
            PYTHON: `class MedianFinder:
    def __init__(self):
        # Your code here
    
    def addNum(self, num):
        # Your code here
    
    def findMedian(self):
        # Your code here`,
            JAVASCRIPT: `class MedianFinder {
    constructor() {
        // Your code here
    }
    
    addNum(num) {
        // Your code here
    }
    
    findMedian() {
        // Your code here
    }
}`,
            JAVA: `class MedianFinder {
    public MedianFinder() {
        // Your code here
    }
    
    public void addNum(int num) {
        // Your code here
    }
    
    public double findMedian() {
        // Your code here
    }
}`,
            CPP: `class MedianFinder {
public:
    MedianFinder() {
        // Your code here
    }
    
    void addNum(int num) {
        // Your code here
    }
    
    double findMedian() {
        // Your code here
    }
};`
        },
        timeLimitMs: 3000,
        memoryLimitMb: 512
    },
    {
        slug: 'word-break',
        title: 'Word Break',
        difficulty: Difficulty.HARD,
        tags: ['string', 'dynamic-programming'],
        supportedLanguages: ['PYTHON', 'JAVASCRIPT', 'JAVA', 'CPP'],
        statement: `Given a string s and a dictionary of strings wordDict, return true if s can be segmented into a space-separated sequence of one or more dictionary words.

Note that the same word in the dictionary may be reused multiple times in the segmentation.`,
        inputFormat: `First line: string s
Second line: n (number of words in dictionary)
Next n lines: words`,
        outputFormat: `Print "true" if string can be segmented, otherwise print "false".`,
        constraints: `1 <= s.length <= 300
1 <= wordDict.length <= 1000`,
        sampleInput: `applepenapple
2
apple
pen`,
        sampleOutput: `true`,
        explanation: `Use DP: dp[i] = true if s[:i] can be segmented. Check all possible splits at position i.`,
        starterCodes: {
            PYTHON: `def word_break(s, word_dict):
    # Your code here
    pass`,
            JAVASCRIPT: `function wordBreak(s, wordDict) {
    // Your code here
}`,
            JAVA: `class Solution {
    public boolean wordBreak(String s, List<String> wordDict) {
        // Your code here
    }
}`,
            CPP: `class Solution {
public:
    bool wordBreak(string s, vector<string>& wordDict) {
        // Your code here
    }
};`
        },
        timeLimitMs: 3000,
        memoryLimitMb: 512
    },
    {
        slug: 'minimum-window-substring',
        title: 'Minimum Window Substring',
        difficulty: Difficulty.HARD,
        tags: ['string', 'sliding-window'],
        supportedLanguages: ['PYTHON', 'JAVASCRIPT', 'JAVA', 'CPP'],
        statement: `Given two strings s and t of lengths m and n respectively, return the minimum window substring of s such that every character in t (including duplicates) is included in the window.

If there is no such substring, return the empty string.`,
        inputFormat: `Two lines:
First line: string s
Second line: string t`,
        outputFormat: `Print the minimum window substring, or empty string if none exists.`,
        constraints: `m, n <= 10^5`,
        sampleInput: `ADOBECODEBANCODE
ABC`,
        sampleOutput: `BANC`,
        explanation: `Use sliding window with character frequency count. Expand window to include all required chars, then shrink from left.`,
        starterCodes: {
            PYTHON: `def min_window(s, t):
    # Your code here
    pass`,
            JAVASCRIPT: `function minWindow(s, t) {
    // Your code here
}`,
            JAVA: `class Solution {
    public String minWindow(String s, String t) {
        // Your code here
    }
}`,
            CPP: `class Solution {
public:
    string minWindow(string s, string t) {
        // Your code here
    }
};`
        },
        timeLimitMs: 3000,
        memoryLimitMb: 512
    },
    {
        slug: 'largest-rectangle',
        title: 'Largest Rectangle in Histogram',
        difficulty: Difficulty.HARD,
        tags: ['stack', 'array'],
        supportedLanguages: ['PYTHON', 'JAVASCRIPT', 'JAVA', 'CPP'],
        statement: `Given an array of integers heights representing the histogram's bar height where the width of each bar is 1, return the area of the largest rectangle in the histogram.`,
        inputFormat: `First line contains n.
Second line contains n space-separated integers.`,
        outputFormat: `Print the maximum rectangle area.`,
        constraints: `1 <= heights.length <= 10^4`,
        sampleInput: `6
2 1 5 6 2 3`,
        sampleOutput: `10`,
        explanation: `Use stack to keep track of increasing heights. Calculate area when popping from stack.`,
        starterCodes: {
            PYTHON: `def largest_rectangle_area(heights):
    # Your code here
    pass`,
            JAVASCRIPT: `function largestRectangleArea(heights) {
    // Your code here
}`,
            JAVA: `class Solution {
    public int largestRectangleArea(int[] heights) {
        // Your code here
    }
}`,
            CPP: `class Solution {
public:
    int largestRectangleArea(vector<int>& heights) {
        // Your code here
    }
};`
        },
        timeLimitMs: 3000,
        memoryLimitMb: 512
    }
];
async function seedDSAProblems() {
    console.log('Seeding DSA problems...');
    for (const problem of dsaProblems) {
        try {
            // Create problem
            const createdProblem = await prisma.problem.create({
                data: {
                    slug: problem.slug,
                    title: problem.title,
                    difficulty: problem.difficulty,
                    tags: JSON.stringify(problem.tags),
                    supportedLanguages: JSON.stringify(problem.supportedLanguages),
                    statement: problem.statement,
                    inputFormat: problem.inputFormat,
                    outputFormat: problem.outputFormat,
                    constraints: problem.constraints,
                    sampleInput: problem.sampleInput,
                    sampleOutput: problem.sampleOutput,
                    explanation: problem.explanation,
                    starterCodes: JSON.stringify(problem.starterCodes),
                    timeLimitMs: problem.timeLimitMs,
                    memoryLimitMb: problem.memoryLimitMb
                }
            });
            // Create test cases
            const testCases = [
                {
                    input: problem.sampleInput,
                    output: problem.sampleOutput,
                    isHidden: false
                }
            ];
            // Add hidden test cases for some problems
            if (problem.slug === 'two-sum') {
                testCases.push({ input: '3\n1 2 4\n6', output: '1 2', isHidden: true }, { input: '3\n3 2 4\n6', output: '-1', isHidden: true });
            }
            else if (problem.slug === 'valid-parentheses') {
                testCases.push({ input: '([{}])', output: 'true', isHidden: true }, { input: '([)]', output: 'false', isHidden: true });
            }
            for (const testCase of testCases) {
                await prisma.testCase.create({
                    data: {
                        problemId: createdProblem.id,
                        input: testCase.input,
                        output: testCase.output,
                        isHidden: testCase.isHidden
                    }
                });
            }
            console.log(`Created problem: ${problem.title} (${problem.difficulty})`);
        }
        catch (error) {
            console.error(`Error creating problem ${problem.slug}:`, error);
        }
    }
    console.log('DSA problems seeded successfully!');
}
seedDSAProblems()
    .catch(console.error)
    .finally(() => prisma.$disconnect());
