import bcrypt from "bcryptjs";
import { PrismaClient, Difficulty, Language, Role } from "@prisma/client";
const prisma = new PrismaClient();
const starterCodes = {
    C: `#include <stdio.h>\n\nint main() {\n    // Write your code here\n    return 0;\n}`,
    CPP: `#include <bits/stdc++.h>\nusing namespace std;\n\nint main() {\n    // Write your code here\n    return 0;\n}`,
    PYTHON: `# Write your code here\n`,
    JAVA: `import java.io.*;\nimport java.util.*;\n\npublic class Main {\n    public static void main(String[] args) throws Exception {\n        // Write your code here\n    }\n}`,
    JAVASCRIPT: `// Write your JavaScript code here\nconst readline = require('readline');\nconst rl = readline.createInterface({ input: process.stdin, output: process.stdout });\nrl.on('line', (line) => {\n    // Process input\n});\n`,
    HTML: `<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <title>Solution</title>\n</head>\n<body>\n    <!-- Write your HTML here -->\n</body>\n</html>\n`,
    CSS: `/* Write your CSS here */\nbody {\n    margin: 0;\n    padding: 0;\n}\n`
};
function lcg(seed) {
    let state = (seed % 2147483647) || 1;
    return () => {
        state = (state * 48271) % 2147483647;
        return state;
    };
}
function randInt(next, min, max) {
    return min + (next() % (max - min + 1));
}
function makeArray(seed, n, min = -20, max = 50) {
    const next = lcg(seed);
    return Array.from({ length: n }, () => randInt(next, min, max));
}
function normalizeSpace(text) {
    return text.trim().replace(/\s+/g, " ");
}
function countWords(text) {
    const v = text.trim();
    if (!v)
        return 0;
    return v.split(/\s+/).length;
}
function gcd(a, b) {
    let x = Math.abs(a);
    let y = Math.abs(b);
    while (y !== 0) {
        const t = x % y;
        x = y;
        y = t;
    }
    return x;
}
function modPow(a, b, m) {
    let base = BigInt(a) % BigInt(m);
    let exp = BigInt(b);
    let mod = BigInt(m);
    let ans = 1n;
    while (exp > 0n) {
        if (exp & 1n)
            ans = (ans * base) % mod;
        base = (base * base) % mod;
        exp >>= 1n;
    }
    return Number(ans);
}
function climbWays(n) {
    if (n <= 1)
        return 1;
    let a = 1;
    let b = 1;
    for (let i = 2; i <= n; i++) {
        const c = a + b;
        a = b;
        b = c;
    }
    return b;
}
function minStepsToOne(n) {
    const dp = Array(n + 1).fill(Number.MAX_SAFE_INTEGER);
    dp[1] = 0;
    for (let i = 2; i <= n; i++) {
        dp[i] = Math.min(dp[i], dp[i - 1] + 1);
        if (i % 2 === 0)
            dp[i] = Math.min(dp[i], dp[i / 2] + 1);
        if (i % 3 === 0)
            dp[i] = Math.min(dp[i], dp[i / 3] + 1);
    }
    return dp[n];
}
function nextGreaterToLeft(arr) {
    const st = [];
    const out = [];
    for (const v of arr) {
        while (st.length && st[st.length - 1] <= v)
            st.pop();
        out.push(st.length ? st[st.length - 1] : -1);
        st.push(v);
    }
    return out;
}
function isBalancedBrackets(s) {
    const st = [];
    const open = new Set(["(", "[", "{"]);
    const closeMap = {
        ")": "(",
        "]": "[",
        "}": "{"
    };
    for (const ch of s) {
        if (open.has(ch))
            st.push(ch);
        else {
            if (!st.length || st.pop() !== closeMap[ch])
                return false;
        }
    }
    return st.length === 0;
}
function buildGraph(seed, n, m) {
    const next = lcg(seed);
    const edges = [];
    const seen = new Set();
    let attempts = 0;
    while (edges.length < m && attempts < m * 20) {
        attempts++;
        const u = randInt(next, 1, n);
        const v = randInt(next, 1, n);
        if (u === v)
            continue;
        const a = Math.min(u, v);
        const b = Math.max(u, v);
        const key = `${a}-${b}`;
        if (seen.has(key))
            continue;
        seen.add(key);
        edges.push([a, b]);
    }
    return edges;
}
function countComponents(n, edges) {
    const parent = Array.from({ length: n + 1 }, (_, i) => i);
    const find = (x) => {
        while (parent[x] !== x) {
            parent[x] = parent[parent[x]];
            x = parent[x];
        }
        return x;
    };
    const union = (a, b) => {
        const pa = find(a);
        const pb = find(b);
        if (pa !== pb)
            parent[pb] = pa;
    };
    for (const [u, v] of edges)
        union(u, v);
    const roots = new Set();
    for (let i = 1; i <= n; i++)
        roots.add(find(i));
    return roots.size;
}
function countTreeLeaves(parents) {
    const n = parents.length;
    const hasChild = Array(n).fill(false);
    for (let i = 1; i < n; i++) {
        hasChild[parents[i]] = true;
    }
    let leaves = 0;
    for (let i = 0; i < n; i++) {
        if (!hasChild[i])
            leaves++;
    }
    return leaves;
}
function makeRandomString(seed, length) {
    const next = lcg(seed);
    const chars = "abcdefghijklmnopqrstuvwxyz";
    let out = "";
    for (let i = 0; i < length; i++) {
        out += chars[randInt(next, 0, chars.length - 1)];
    }
    return out;
}
const templates = [
    {
        key: "array-sum",
        title: "Array Sum",
        tags: ["Arrays", "Basics"],
        statement: "Given an integer array, print the sum of all elements.",
        inputFormat: "First line N. Second line N integers.",
        outputFormat: "Print one integer, the sum.",
        constraints: "1 <= N <= 2e5",
        explanation: "Accumulate values using a running total.",
        makeCase: (seed) => {
            const n = 6 + (seed % 5);
            const arr = makeArray(seed, n, -25, 60);
            const sum = arr.reduce((a, b) => a + b, 0);
            return { input: `${n}\n${arr.join(" ")}`, output: `${sum}` };
        }
    },
    {
        key: "array-maximum",
        title: "Maximum in Array",
        tags: ["Arrays"],
        statement: "Find the maximum value in the given array.",
        inputFormat: "First line N. Second line N integers.",
        outputFormat: "Print the maximum integer.",
        constraints: "1 <= N <= 2e5",
        explanation: "Track the largest number while scanning once.",
        makeCase: (seed) => {
            const n = 5 + (seed % 6);
            const arr = makeArray(seed + 11, n, -80, 120);
            const mx = Math.max(...arr);
            return { input: `${n}\n${arr.join(" ")}`, output: `${mx}` };
        }
    },
    {
        key: "count-even",
        title: "Count Even Numbers",
        tags: ["Arrays", "Math"],
        statement: "Count how many elements in the array are even.",
        inputFormat: "First line N. Second line N integers.",
        outputFormat: "Print one integer count.",
        constraints: "1 <= N <= 2e5",
        explanation: "Check each value with value % 2 == 0.",
        makeCase: (seed) => {
            const n = 7 + (seed % 4);
            const arr = makeArray(seed + 21, n, -30, 70);
            const c = arr.filter((x) => x % 2 === 0).length;
            return { input: `${n}\n${arr.join(" ")}`, output: `${c}` };
        }
    },
    {
        key: "rotate-array-right",
        title: "Rotate Array Right",
        tags: ["Arrays", "Two Pointers"],
        statement: "Rotate the array to the right by K positions.",
        inputFormat: "First line N K. Second line N integers.",
        outputFormat: "Print rotated array.",
        constraints: "1 <= N <= 2e5",
        explanation: "Use K % N and shift suffix to front.",
        makeCase: (seed) => {
            const n = 6 + (seed % 5);
            const arr = makeArray(seed + 31, n, 0, 40);
            const k = (seed % (n + 2)) + 1;
            const shift = k % n;
            const rot = arr.slice(n - shift).concat(arr.slice(0, n - shift));
            return { input: `${n} ${k}\n${arr.join(" ")}`, output: rot.join(" ") };
        }
    },
    {
        key: "range-sum",
        title: "Single Range Sum",
        tags: ["Arrays", "Prefix Sum"],
        statement: "Given array and 1-indexed L, R, print sum from L to R.",
        inputFormat: "First line N. Second line N integers. Third line L R.",
        outputFormat: "Print range sum.",
        constraints: "1 <= L <= R <= N",
        explanation: "Sum selected segment directly or via prefix sum.",
        makeCase: (seed) => {
            const n = 8 + (seed % 4);
            const arr = makeArray(seed + 41, n, -20, 35);
            const next = lcg(seed + 53);
            let l = randInt(next, 1, n);
            let r = randInt(next, l, n);
            const sum = arr.slice(l - 1, r).reduce((a, b) => a + b, 0);
            return { input: `${n}\n${arr.join(" ")}\n${l} ${r}`, output: `${sum}` };
        }
    },
    {
        key: "reverse-string",
        title: "Reverse a String",
        tags: ["Strings", "Basics"],
        statement: "Print the reverse of the input lowercase string.",
        inputFormat: "One line string S.",
        outputFormat: "Print reversed string.",
        constraints: "1 <= |S| <= 2e5",
        explanation: "Traverse string from end to start.",
        makeCase: (seed) => {
            const s = makeRandomString(seed + 61, 6 + (seed % 7));
            return { input: s, output: s.split("").reverse().join("") };
        }
    },
    {
        key: "palindrome-check",
        title: "Palindrome Check",
        tags: ["Strings", "Two Pointers"],
        statement: "Print YES if S is palindrome else NO.",
        inputFormat: "One line string S.",
        outputFormat: "YES or NO.",
        constraints: "1 <= |S| <= 2e5",
        explanation: "Compare mirrored characters.",
        makeCase: (seed) => {
            const makePal = seed % 2 === 0;
            const half = makeRandomString(seed + 71, 4 + (seed % 4));
            const s = makePal ? half + half.split("").reverse().join("") : half + "z";
            const out = s === s.split("").reverse().join("") ? "YES" : "NO";
            return { input: s, output: out };
        }
    },
    {
        key: "vowel-count",
        title: "Count Vowels",
        tags: ["Strings"],
        statement: "Count vowels (a,e,i,o,u) in the given lowercase string.",
        inputFormat: "One line string S.",
        outputFormat: "Print integer count.",
        constraints: "1 <= |S| <= 2e5",
        explanation: "Check membership in vowel set.",
        makeCase: (seed) => {
            const s = makeRandomString(seed + 81, 8 + (seed % 7));
            const c = s.split("").filter((ch) => "aeiou".includes(ch)).length;
            return { input: s, output: `${c}` };
        }
    },
    {
        key: "word-count",
        title: "Word Counter",
        tags: ["Strings"],
        statement: "Count words in a sentence separated by spaces.",
        inputFormat: "One line sentence.",
        outputFormat: "Print integer word count.",
        constraints: "Sentence length <= 500",
        explanation: "Split by one or more spaces after trimming.",
        makeCase: (seed) => {
            const words = ["code", "sprint", "daily", "arrays", "graph", "dp", "stack", "tree", "path", "logic"];
            const next = lcg(seed + 91);
            const k = 4 + (seed % 5);
            const out = [];
            for (let i = 0; i < k; i++)
                out.push(words[randInt(next, 0, words.length - 1)]);
            const sentence = out.join(" ");
            return { input: sentence, output: `${countWords(sentence)}` };
        }
    },
    {
        key: "char-frequency",
        title: "Character Frequency",
        tags: ["Strings", "Hashing"],
        statement: "Given string S and character C, print frequency of C in S.",
        inputFormat: "First line S. Second line character C.",
        outputFormat: "Print frequency count.",
        constraints: "1 <= |S| <= 2e5",
        explanation: "Scan and count exact matches.",
        makeCase: (seed) => {
            const s = makeRandomString(seed + 101, 10 + (seed % 8));
            const idx = seed % s.length;
            const c = s[idx];
            const freq = s.split("").filter((x) => x === c).length;
            return { input: `${s}\n${c}`, output: `${freq}` };
        }
    },
    {
        key: "fibonacci-n",
        title: "Nth Fibonacci",
        tags: ["DP", "Recursion"],
        statement: "Given N, print Fibonacci number F(N) with F0=0, F1=1.",
        inputFormat: "One integer N.",
        outputFormat: "Print F(N).",
        constraints: "0 <= N <= 45",
        explanation: "Build sequence iteratively.",
        makeCase: (seed) => {
            const n = 5 + (seed % 25);
            let a = 0;
            let b = 1;
            for (let i = 0; i < n; i++) {
                const c = a + b;
                a = b;
                b = c;
            }
            return { input: `${n}`, output: `${a}` };
        }
    },
    {
        key: "gcd-two",
        title: "Greatest Common Divisor",
        tags: ["Math"],
        statement: "Given A and B, print gcd(A,B).",
        inputFormat: "One line with A B.",
        outputFormat: "Print gcd.",
        constraints: "1 <= A,B <= 1e9",
        explanation: "Use Euclidean algorithm.",
        makeCase: (seed) => {
            const next = lcg(seed + 111);
            const a = randInt(next, 10, 600);
            const b = randInt(next, 10, 600);
            return { input: `${a} ${b}`, output: `${gcd(a, b)}` };
        }
    },
    {
        key: "power-mod",
        title: "Power Mod",
        tags: ["Math", "Binary Exponentiation"],
        statement: "Compute (A^B) mod M.",
        inputFormat: "One line A B M.",
        outputFormat: "Print modular power.",
        constraints: "1 <= A,B <= 1e9; 2 <= M <= 1e9+7",
        explanation: "Use fast exponentiation by squaring.",
        makeCase: (seed) => {
            const next = lcg(seed + 121);
            const a = randInt(next, 2, 50);
            const b = randInt(next, 4, 30);
            const m = randInt(next, 97, 1009);
            return { input: `${a} ${b} ${m}`, output: `${modPow(a, b, m)}` };
        }
    },
    {
        key: "climb-stairs",
        title: "Climb Stairs Ways",
        tags: ["DP"],
        statement: "From step 0 to N, you can move 1 or 2 steps. Count total ways.",
        inputFormat: "One integer N.",
        outputFormat: "Print number of ways.",
        constraints: "0 <= N <= 45",
        explanation: "dp[i] = dp[i-1] + dp[i-2].",
        makeCase: (seed) => {
            const n = 4 + (seed % 30);
            return { input: `${n}`, output: `${climbWays(n)}` };
        }
    },
    {
        key: "min-steps-one",
        title: "Min Steps to One",
        tags: ["DP", "Recursion"],
        statement: "Reduce N to 1 using operations: -1, /2 (if divisible), /3 (if divisible). Print minimum steps.",
        inputFormat: "One integer N.",
        outputFormat: "Print minimum steps.",
        constraints: "1 <= N <= 2000",
        explanation: "Use bottom-up DP over states 1..N.",
        makeCase: (seed) => {
            const n = 10 + (seed % 120);
            return { input: `${n}`, output: `${minStepsToOne(n)}` };
        }
    },
    {
        key: "next-greater-left",
        title: "Nearest Greater on Left",
        tags: ["Stack", "Arrays"],
        statement: "For each element, print nearest greater element on its left, else -1.",
        inputFormat: "First line N. Second line N integers.",
        outputFormat: "Print N integers.",
        constraints: "1 <= N <= 2e5",
        explanation: "Maintain decreasing stack of previous elements.",
        makeCase: (seed) => {
            const n = 6 + (seed % 7);
            const arr = makeArray(seed + 131, n, 1, 80);
            const out = nextGreaterToLeft(arr).join(" ");
            return { input: `${n}\n${arr.join(" ")}`, output: out };
        }
    },
    {
        key: "balanced-brackets",
        title: "Balanced Brackets",
        tags: ["Stack", "Strings"],
        statement: "Given bracket string with (), {}, [], print YES if balanced else NO.",
        inputFormat: "One line bracket string.",
        outputFormat: "YES or NO.",
        constraints: "1 <= |S| <= 2e5",
        explanation: "Use stack and pair matching.",
        makeCase: (seed) => {
            const patterns = ["([]){}", "([{}])", "([)]", "(((())))", "{[()()]}", "{[(])}"];
            const s = patterns[seed % patterns.length];
            return { input: s, output: isBalancedBrackets(s) ? "YES" : "NO" };
        }
    },
    {
        key: "graph-degree",
        title: "Degree of a Node",
        tags: ["Graphs", "Basics"],
        statement: "Given an undirected graph, print degree of node X.",
        inputFormat: "First line N M. Next M lines U V. Last line X.",
        outputFormat: "Print degree of X.",
        constraints: "1 <= N <= 1e5",
        explanation: "Count edges that touch X.",
        makeCase: (seed) => {
            const next = lcg(seed + 141);
            const n = randInt(next, 5, 9);
            const m = randInt(next, n - 1, Math.min(n * (n - 1) / 2, n + 5));
            const edges = buildGraph(seed + 151, n, m);
            const x = randInt(next, 1, n);
            let degree = 0;
            for (const [u, v] of edges)
                if (u === x || v === x)
                    degree++;
            const edgeLines = edges.map(([u, v]) => `${u} ${v}`).join("\n");
            return { input: `${n} ${edges.length}\n${edgeLines}\n${x}`, output: `${degree}` };
        }
    },
    {
        key: "connected-components",
        title: "Connected Components Count",
        tags: ["Graphs", "BFS", "DFS"],
        statement: "Given undirected graph, print number of connected components.",
        inputFormat: "First line N M. Next M lines U V.",
        outputFormat: "Print component count.",
        constraints: "1 <= N <= 2e5",
        explanation: "Traverse graph and count DFS/BFS starts.",
        makeCase: (seed) => {
            const next = lcg(seed + 161);
            const n = randInt(next, 6, 11);
            const m = randInt(next, 3, Math.min(12, n * (n - 1) / 2));
            const edges = buildGraph(seed + 171, n, m);
            const comps = countComponents(n, edges);
            const edgeLines = edges.map(([u, v]) => `${u} ${v}`).join("\n");
            return { input: `${n} ${edges.length}\n${edgeLines}`, output: `${comps}` };
        }
    },
    {
        key: "tree-leaf-count",
        title: "Count Leaves in Rooted Tree",
        tags: ["Trees", "DFS"],
        statement: "Given parent array of a rooted tree (parent[0] = -1), print number of leaf nodes.",
        inputFormat: "First line N. Second line N integers parent array.",
        outputFormat: "Print leaf count.",
        constraints: "1 <= N <= 2e5",
        explanation: "A node is leaf if it has no children.",
        makeCase: (seed) => {
            const next = lcg(seed + 181);
            const n = randInt(next, 6, 12);
            const parent = Array(n).fill(0);
            parent[0] = -1;
            for (let i = 1; i < n; i++) {
                parent[i] = randInt(next, 0, i - 1);
            }
            const leaves = countTreeLeaves(parent);
            return { input: `${n}\n${parent.join(" ")}`, output: `${leaves}` };
        }
    },
    {
        key: "activity-selection",
        title: "Maximum Non-overlapping Activities",
        tags: ["Greedy", "Sorting"],
        statement: "Given start/end times of activities, choose maximum non-overlapping activities.",
        inputFormat: "First line N. Next N lines S E.",
        outputFormat: "Print maximum count.",
        constraints: "1 <= N <= 2e5",
        explanation: "Sort by end time and greedily pick compatible activities.",
        makeCase: (seed) => {
            const next = lcg(seed + 191);
            const n = randInt(next, 5, 9);
            const acts = [];
            for (let i = 0; i < n; i++) {
                const s = randInt(next, 0, 18);
                const e = s + randInt(next, 1, 6);
                acts.push([s, e]);
            }
            const sorted = [...acts].sort((a, b) => a[1] - b[1]);
            let count = 0;
            let lastEnd = -1;
            for (const [s, e] of sorted) {
                if (s >= lastEnd) {
                    count++;
                    lastEnd = e;
                }
            }
            const lines = acts.map(([s, e]) => `${s} ${e}`).join("\n");
            return { input: `${n}\n${lines}`, output: `${count}` };
        }
    },
    // ===== HTML Problems =====
    {
        key: "html-structure",
        title: "HTML Page Structure",
        tags: ["HTML", "Basics"],
        statement: "Create a valid HTML5 page with DOCTYPE, html, head (with meta charset and title), and body (with an h1 heading). The title should be 'My Page' and heading 'Welcome'.",
        inputFormat: "No input required.",
        outputFormat: "A complete HTML5 document with proper structure.",
        constraints: "Use HTML5 semantic structure. Include DOCTYPE declaration.",
        explanation: "Every HTML5 page needs DOCTYPE, html, head with meta charset and title, and body with content.",
        makeCase: (seed) => {
            return { input: "none", output: "Valid HTML5 with DOCTYPE, html, head, body, h1" };
        }
    },
    {
        key: "html-lists",
        title: "HTML Ordered & Unordered Lists",
        tags: ["HTML", "Lists"],
        statement: "Create an HTML page with an ordered list of 3 items (Apple, Banana, Cherry) and an unordered list of 3 items (Dog, Cat, Fish). Wrap each in a section with an h2 heading.",
        inputFormat: "No input required.",
        outputFormat: "HTML with ol and ul elements, each inside a section.",
        constraints: "Use proper list tags: ol, ul, li. Each list must have exactly 3 items.",
        explanation: "Use <ol> for ordered lists and <ul> for unordered lists. Each item uses <li>.",
        makeCase: (seed) => {
            return { input: "none", output: "HTML with ordered and unordered lists" };
        }
    },
    {
        key: "html-form",
        title: "HTML Form Creation",
        tags: ["HTML", "Forms"],
        statement: "Create an HTML form with: a text input for name, an email input, a password input, a select dropdown with 3 options (Student, Professional, Other), and a submit button. Include labels for each field.",
        inputFormat: "No input required.",
        outputFormat: "HTML form with all required input elements and labels.",
        constraints: "Use proper form elements: form, input, select, option, label, button.",
        explanation: "Forms collect user input. Each input should have an associated label for accessibility.",
        makeCase: (seed) => {
            return { input: "none", output: "HTML form with text, email, password, select, and submit" };
        }
    },
    {
        key: "html-table",
        title: "HTML Data Table",
        tags: ["HTML", "Tables"],
        statement: "Create an HTML table with 3 columns (Name, Age, City) and 2 data rows. Include a thead with column headers and tbody for data. Use semantic table elements.",
        inputFormat: "No input required.",
        outputFormat: "HTML table with thead, tbody, and 2 rows of data.",
        constraints: "Use table, thead, tbody, tr, th, td elements.",
        explanation: "Tables display tabular data. Use thead for headers and tbody for data rows.",
        makeCase: (seed) => {
            return { input: "none", output: "HTML table with headers and 2 data rows" };
        }
    },
    {
        key: "html-semantic",
        title: "HTML5 Semantic Layout",
        tags: ["HTML", "Semantic"],
        statement: "Create an HTML5 page using semantic elements: header with nav, main with article and aside, and footer. Include a navigation link in the nav element.",
        inputFormat: "No input required.",
        outputFormat: "HTML5 with header, nav, main, article, aside, footer.",
        constraints: "Use only HTML5 semantic elements, not div for layout sections.",
        explanation: "Semantic HTML5 elements like header, nav, main, article, aside, footer improve accessibility and SEO.",
        makeCase: (seed) => {
            return { input: "none", output: "HTML5 semantic layout with header, nav, main, article, aside, footer" };
        }
    },
    // ===== CSS Problems =====
    {
        key: "css-selectors",
        title: "CSS Selectors & Styling",
        tags: ["CSS", "Basics"],
        statement: "Write CSS rules to: set body background to #f5f5f5, make all h1 elements blue and centered, give all paragraphs 16px font-size and line-height of 1.5, and add 20px padding to elements with class 'container'.",
        inputFormat: "No input required.",
        outputFormat: "CSS rules for body, h1, p, and .container.",
        constraints: "Use element selectors and class selectors. Do not use inline styles.",
        explanation: "CSS selectors target HTML elements. Element selectors target tags, class selectors use a dot prefix.",
        makeCase: (seed) => {
            return { input: "none", output: "CSS with body, h1, p, and .container rules" };
        }
    },
    {
        key: "css-flexbox",
        title: "CSS Flexbox Layout",
        tags: ["CSS", "Flexbox"],
        statement: "Write CSS for a flex container (.flex-container) that displays items in a row, wraps them, centers items on the cross axis, and distributes space evenly with a 10px gap.",
        inputFormat: "No input required.",
        outputFormat: "CSS flexbox rules for .flex-container.",
        constraints: "Use display: flex and related flex properties.",
        explanation: "Flexbox provides efficient layout. Use justify-content for main axis, align-items for cross axis, flex-wrap for wrapping, and gap for spacing.",
        makeCase: (seed) => {
            return { input: "none", output: "CSS flexbox with row, wrap, center, gap" };
        }
    },
    {
        key: "css-grid",
        title: "CSS Grid Layout",
        tags: ["CSS", "Grid"],
        statement: "Write CSS for a grid container (.grid-layout) with 3 equal columns, 20px gap, and a minimum row height of 200px. Items should stretch to fill their cells.",
        inputFormat: "No input required.",
        outputFormat: "CSS grid rules for .grid-layout.",
        constraints: "Use display: grid with grid-template-columns and gap.",
        explanation: "CSS Grid creates two-dimensional layouts. Use grid-template-columns with repeat and fr units.",
        makeCase: (seed) => {
            return { input: "none", output: "CSS grid with 3 columns, 20px gap, 200px min row height" };
        }
    },
    {
        key: "css-responsive",
        title: "CSS Responsive Design",
        tags: ["CSS", "Responsive", "Media Queries"],
        statement: "Write a media query that: when screen width is 768px or less, changes .container width to 100%, sets .sidebar display to none, and makes .grid-layout a single column.",
        inputFormat: "No input required.",
        outputFormat: "CSS with @media rule for max-width 768px.",
        constraints: "Use @media (max-width: 768px) syntax.",
        explanation: "Media queries apply styles based on device characteristics. Use max-width for mobile-first breakpoints.",
        makeCase: (seed) => {
            return { input: "none", output: "CSS media query for responsive layout" };
        }
    },
    {
        key: "css-animations",
        title: "CSS Animations",
        tags: ["CSS", "Animations"],
        statement: "Write CSS to create a keyframe animation called 'fadeIn' that goes from opacity 0 to opacity 1 over 2 seconds. Apply it to elements with class .fade-in using animation: fadeIn 2s ease-in.",
        inputFormat: "No input required.",
        outputFormat: "CSS with @keyframes fadeIn and .fade-in class.",
        constraints: "Use @keyframes and animation property.",
        explanation: "@keyframes defines animation stages. The animation property applies it to elements with duration and timing function.",
        makeCase: (seed) => {
            return { input: "none", output: "CSS keyframe animation fadeIn applied to .fade-in" };
        }
    },
    // ===== JavaScript Problems =====
    {
        key: "js-variable-types",
        title: "JavaScript Variables & Types",
        tags: ["JavaScript", "Basics"],
        statement: "Write a JavaScript program that reads a line of integers separated by spaces, stores them in an array using const, and prints the sum and the count of elements.",
        inputFormat: "One line of space-separated integers.",
        outputFormat: "Print sum and count separated by space.",
        constraints: "1 <= number of integers <= 100, -1000 <= each integer <= 1000",
        explanation: "Use const for array declaration, split() to parse, and reduce() to sum.",
        makeCase: (seed) => {
            const n = 4 + (seed % 5);
            const arr = makeArray(seed + 200, n, -50, 100);
            const sum = arr.reduce((a, b) => a + b, 0);
            return { input: arr.join(" "), output: `${sum} ${n}` };
        }
    },
    {
        key: "js-array-methods",
        title: "JavaScript Array Methods",
        tags: ["JavaScript", "Arrays"],
        statement: "Write a JavaScript program that reads an array of integers, filters out the odd numbers, doubles each remaining even number, and prints the result array.",
        inputFormat: "First line N. Second line N space-separated integers.",
        outputFormat: "Print filtered and doubled array, space-separated.",
        constraints: "1 <= N <= 100",
        explanation: "Use filter() to keep evens, then map() to double each.",
        makeCase: (seed) => {
            const n = 5 + (seed % 5);
            const arr = makeArray(seed + 210, n, 1, 20);
            const evensDoubled = arr.filter(x => x % 2 === 0).map(x => x * 2);
            return { input: `${n}\n${arr.join(" ")}`, output: evensDoubled.length ? evensDoubled.join(" ") : "EMPTY" };
        }
    },
    {
        key: "js-string-methods",
        title: "JavaScript String Manipulation",
        tags: ["JavaScript", "Strings"],
        statement: "Write a JavaScript program that reads a sentence and prints: the sentence in uppercase, the number of words, and the sentence with all spaces replaced by hyphens.",
        inputFormat: "One line sentence.",
        outputFormat: "Print uppercase version, word count, and hyphenated version on separate lines.",
        constraints: "Sentence length <= 500",
        explanation: "Use toUpperCase(), split(/\\s+/).length, and replaceAll() or replace(/\\s+/g, '-').",
        makeCase: (seed) => {
            const words = ["hello", "world", "javascript", "coding", "practice", "skill", "up", "build"];
            const next = lcg(seed + 220);
            const k = 3 + (seed % 4);
            const out = [];
            for (let i = 0; i < k; i++)
                out.push(words[randInt(next, 0, words.length - 1)]);
            const sentence = out.join(" ");
            const upper = sentence.toUpperCase();
            const count = sentence.trim().split(/\s+/).length;
            const hyphenated = sentence.replace(/\s+/g, "-");
            return { input: sentence, output: `${upper}\n${count}\n${hyphenated}` };
        }
    },
    {
        key: "js-object-basics",
        title: "JavaScript Object Operations",
        tags: ["JavaScript", "Objects"],
        statement: "Write a JavaScript program that reads N key-value pairs (key and integer value on each line), stores them in an object, then reads a key and prints its value or 'NOT FOUND' if the key doesn't exist.",
        inputFormat: "First line N. Next N lines: key value. Last line: query key.",
        outputFormat: "Print value or NOT FOUND.",
        constraints: "1 <= N <= 50, key length <= 20",
        explanation: "Use an object or Map to store key-value pairs, then check with hasOwnProperty or in operator.",
        makeCase: (seed) => {
            const next = lcg(seed + 230);
            const n = 3 + (seed % 4);
            const pairs = [];
            const obj = {};
            for (let i = 0; i < n; i++) {
                const key = `key${randInt(next, 1, 20)}`;
                const val = randInt(next, 1, 100);
                pairs.push([key, val]);
                obj[key] = val;
            }
            const queryIdx = seed % (n + 1);
            const queryKey = queryIdx < n ? pairs[queryIdx][0] : "key99";
            const result = obj[queryKey] !== undefined ? `${obj[queryKey]}` : "NOT FOUND";
            const input = `${n}\n${pairs.map(([k, v]) => `${k} ${v}`).join("\n")}\n${queryKey}`;
            return { input, output: result };
        }
    },
    {
        key: "js-async-pattern",
        title: "JavaScript Promise & Async",
        tags: ["JavaScript", "Async"],
        statement: "Write a JavaScript function that uses Promises: create a function delay(ms) that returns a Promise resolving after ms milliseconds. Then create an async function process() that awaits delay(100) and prints 'Done after delay'. Read an integer N and print N * 2 after the delay.",
        inputFormat: "One integer N.",
        outputFormat: "Print 'Processing...' then 'Result: N*2'.",
        constraints: "1 <= N <= 1000",
        explanation: "Use new Promise(resolve => setTimeout(resolve, ms)) for delay, and async/await for sequential execution.",
        makeCase: (seed) => {
            const n = 5 + (seed % 20);
            return { input: `${n}`, output: `Processing...\nResult: ${n * 2}` };
        }
    },
    // ===== Java-Specific Problems =====
    {
        key: "java-class-design",
        title: "Java Class & Object Design",
        tags: ["Java", "OOP"],
        statement: "Design a Java class Student with fields: name (String), rollNo (int), marks (int[]). Include a constructor, getter methods, and a method getAverage() that returns the average of marks. Read student details from input and print the average rounded to 2 decimal places.",
        inputFormat: "First line: name. Second line: rollNo. Third line: space-separated marks.",
        outputFormat: "Print average with 2 decimal places.",
        constraints: "1 <= number of marks <= 10, 0 <= each mark <= 100",
        explanation: "Create a class with private fields, constructor, getters, and a method to compute average. Use String.format or printf for 2 decimal places.",
        makeCase: (seed) => {
            const marks = makeArray(seed + 300, 4 + (seed % 5), 0, 100);
            const avg = marks.reduce((a, b) => a + b, 0) / marks.length;
            return { input: `John\n${seed + 1}\n${marks.join(" ")}`, output: avg.toFixed(2) };
        }
    },
    {
        key: "java-inheritance",
        title: "Java Inheritance",
        tags: ["Java", "OOP", "Inheritance"],
        statement: "Create a base class Shape with method area() returning 0. Create subclass Circle with radius field and override area() to return PI*radius*radius. Create subclass Rectangle with length and width, override area() to return length*width. Read type (C/R) and dimensions, print area with 2 decimal places.",
        inputFormat: "First line: C or R. For C: next line radius. For R: next line length width.",
        outputFormat: "Print area with 2 decimal places.",
        constraints: "1 <= radius, length, width <= 100",
        explanation: "Use extends for inheritance and @Override for method overriding. Use Math.PI for accurate PI value.",
        makeCase: (seed) => {
            if (seed % 2 === 0) {
                const r = 1 + (seed % 10);
                return { input: `C\n${r}`, output: (Math.PI * r * r).toFixed(2) };
            }
            else {
                const l = 2 + (seed % 8);
                const w = 1 + (seed % 6);
                return { input: `R\n${l} ${w}`, output: (l * w).toFixed(2) };
            }
        }
    },
    {
        key: "java-collections",
        title: "Java Collections Framework",
        tags: ["Java", "Collections"],
        statement: "Read N integers, store them in an ArrayList, remove duplicates using a HashSet, sort in ascending order, and print the unique sorted numbers.",
        inputFormat: "First line N. Second line N integers.",
        outputFormat: "Print unique sorted integers, space-separated.",
        constraints: "1 <= N <= 100, -1000 <= each integer <= 1000",
        explanation: "Use ArrayList to store, HashSet to remove duplicates, Collections.sort() to sort, then print.",
        makeCase: (seed) => {
            const n = 5 + (seed % 6);
            const arr = makeArray(seed + 310, n, -10, 20);
            const unique = [...new Set(arr)].sort((a, b) => a - b);
            return { input: `${n}\n${arr.join(" ")}`, output: unique.join(" ") };
        }
    },
    {
        key: "java-exception",
        title: "Java Exception Handling",
        tags: ["Java", "Exception Handling"],
        statement: "Read two integers A and B. Compute A/B. If B is 0, catch ArithmeticException and print 'Error: Division by zero'. Otherwise print the result.",
        inputFormat: "One line with A B.",
        outputFormat: "Print result or error message.",
        constraints: "-1000 <= A <= 1000, -100 <= B <= 100",
        explanation: "Use try-catch block around the division. Catch ArithmeticException for division by zero.",
        makeCase: (seed) => {
            const next = lcg(seed + 320);
            const a = randInt(next, -50, 50);
            const b = seed % 3 === 0 ? 0 : randInt(next, 1, 10);
            if (b === 0) {
                return { input: `${a} ${b}`, output: "Error: Division by zero" };
            }
            return { input: `${a} ${b}`, output: `${Math.trunc(a / b)}` };
        }
    },
    // ===== DBMS Problems =====
    {
        key: "sql-select",
        title: "SQL Basic SELECT",
        tags: ["DBMS", "SQL"],
        statement: "Given a table Students(id INT, name VARCHAR, dept VARCHAR, gpa DECIMAL), write a SQL query to find all students in 'CS' department with GPA above 3.5, ordered by name.",
        inputFormat: "No input - write SQL query.",
        outputFormat: "SQL SELECT query.",
        constraints: "Use SELECT, FROM, WHERE, AND, ORDER BY clauses.",
        explanation: "SELECT name, id FROM Students WHERE dept = 'CS' AND gpa > 3.5 ORDER BY name; selects matching rows and orders alphabetically.",
        makeCase: (seed) => {
            return { input: "none", output: "SELECT * FROM Students WHERE dept='CS' AND gpa > 3.5 ORDER BY name" };
        }
    },
    {
        key: "sql-join",
        title: "SQL JOIN Query",
        tags: ["DBMS", "SQL", "Joins"],
        statement: "Given tables: Orders(id, customer_id, amount) and Customers(id, name, city), write a SQL query to show customer name and total order amount for customers who have placed more than 2 orders.",
        inputFormat: "No input - write SQL query.",
        outputFormat: "SQL JOIN query with GROUP BY and HAVING.",
        constraints: "Use JOIN, GROUP BY, HAVING, and aggregate functions.",
        explanation: "JOIN connects tables on customer_id, GROUP BY groups per customer, HAVING filters groups with count > 2, SUM aggregates amounts.",
        makeCase: (seed) => {
            return { input: "none", output: "SELECT c.name, SUM(o.amount) FROM Customers c JOIN Orders o ON c.id=o.customer_id GROUP BY c.id HAVING COUNT(o.id)>2" };
        }
    },
    {
        key: "sql-subquery",
        title: "SQL Subquery",
        tags: ["DBMS", "SQL"],
        statement: "Given Employees(id, name, salary, dept), write a SQL query to find employees who earn more than the average salary of their department.",
        inputFormat: "No input - write SQL query.",
        outputFormat: "SQL query using subquery.",
        constraints: "Use a correlated subquery or JOIN with derived table.",
        explanation: "A correlated subquery references the outer query's dept to compute average per department, then filters employees above that average.",
        makeCase: (seed) => {
            return { input: "none", output: "SELECT * FROM Employees e WHERE salary > (SELECT AVG(salary) FROM Employees WHERE dept=e.dept)" };
        }
    },
    {
        key: "dbms-normalization",
        title: "DBMS Normalization Identify",
        tags: ["DBMS", "Normalization"],
        statement: "Given a relation R(A,B,C,D) with functional dependencies: A->B, B->C, C->D. Identify the highest normal form (1NF, 2NF, 3NF, BCNF). Print the answer.",
        inputFormat: "No input - analyze the FDs.",
        outputFormat: "Print the highest normal form name.",
        constraints: "Analyze candidate keys and partial/transitive dependencies.",
        explanation: "A is the candidate key (A->B, B->C, C->D implies A->ABCD). Since all attributes depend on the full key (no partial deps) and there are transitive deps (A->B->C), it is in 2NF but not 3NF.",
        makeCase: (seed) => {
            const answers = ["2NF", "3NF", "1NF", "BCNF", "2NF"];
            return { input: "none", output: answers[seed % answers.length] };
        }
    },
    {
        key: "dbms-er-model",
        title: "ER Model Design",
        tags: ["DBMS", "ER Model"],
        statement: "Design an ER diagram for a University with: Departments (dept_id, name), Professors (prof_id, name, dept_id), Courses (course_id, title, dept_id). A department has many professors, a professor teaches many courses. Identify the relationships and their cardinalities.",
        inputFormat: "No input - design ER model.",
        outputFormat: "List relationships with cardinalities.",
        constraints: "Use proper entity-relationship notation.",
        explanation: "Department-Professor: 1:N (one dept has many profs). Professor-Course: M:N (one prof teaches many courses, one course can be taught by multiple profs). Department-Course: 1:N.",
        makeCase: (seed) => {
            return { input: "none", output: "Dept-Prof:1:N, Prof-Course:M:N, Dept-Course:1:N" };
        }
    },
    // ===== Data Structures Problems =====
    {
        key: "ds-linked-list-insert",
        title: "Linked List Insertion",
        tags: ["Data Structures", "Linked List"],
        statement: "Given a sequence of integers, simulate inserting each at the end of a singly linked list. Then print the list from head to tail, space-separated.",
        inputFormat: "First line N. Second line N integers.",
        outputFormat: "Print the linked list elements, space-separated.",
        constraints: "1 <= N <= 1000",
        explanation: "Maintain head and tail pointers. Each new node is appended after tail.",
        makeCase: (seed) => {
            const n = 5 + (seed % 6);
            const arr = makeArray(seed + 400, n, 1, 50);
            return { input: `${n}\n${arr.join(" ")}`, output: arr.join(" ") };
        }
    },
    {
        key: "ds-stack-implementation",
        title: "Stack Operations",
        tags: ["Data Structures", "Stack"],
        statement: "Simulate a stack. Read N operations. Each operation is 'push X' or 'pop'. After all operations, print the stack from bottom to top, space-separated. If pop on empty stack, print 'EMPTY'.",
        inputFormat: "First line N. Next N lines: push X or pop.",
        outputFormat: "Print remaining stack bottom to top, or EMPTY.",
        constraints: "1 <= N <= 100, 1 <= X <= 1000",
        explanation: "Use an array as stack. push adds to end, pop removes from end. Track top index.",
        makeCase: (seed) => {
            const next = lcg(seed + 410);
            const n = 4 + (seed % 5);
            const ops = [];
            const stack = [];
            for (let i = 0; i < n; i++) {
                if (stack.length === 0 || next() % 3 !== 0) {
                    const val = randInt(next, 1, 50);
                    ops.push(`push ${val}`);
                    stack.push(val);
                }
                else {
                    ops.push("pop");
                    stack.pop();
                }
            }
            return { input: `${n}\n${ops.join("\n")}`, output: stack.length ? stack.join(" ") : "EMPTY" };
        }
    },
    {
        key: "ds-queue-implementation",
        title: "Queue Operations",
        tags: ["Data Structures", "Queue"],
        statement: "Simulate a queue. Read N operations: 'enqueue X' or 'dequeue'. After all operations, print the queue from front to rear. If dequeue on empty queue, print 'EMPTY'.",
        inputFormat: "First line N. Next N lines: enqueue X or dequeue.",
        outputFormat: "Print remaining queue front to rear, or EMPTY.",
        constraints: "1 <= N <= 100, 1 <= X <= 1000",
        explanation: "Use an array. enqueue adds to end, dequeue removes from front. Track front and rear.",
        makeCase: (seed) => {
            const next = lcg(seed + 420);
            const n = 4 + (seed % 5);
            const ops = [];
            const queue = [];
            for (let i = 0; i < n; i++) {
                if (queue.length === 0 || next() % 3 !== 0) {
                    const val = randInt(next, 1, 50);
                    ops.push(`enqueue ${val}`);
                    queue.push(val);
                }
                else {
                    ops.push("dequeue");
                    queue.shift();
                }
            }
            return { input: `${n}\n${ops.join("\n")}`, output: queue.length ? queue.join(" ") : "EMPTY" };
        }
    },
    {
        key: "ds-binary-tree-height",
        title: "Binary Tree Height",
        tags: ["Data Structures", "Trees"],
        statement: "Given a binary tree as a parent array (parent[i] = parent of node i, -1 for root), print the height of the tree (number of edges on longest root-to-leaf path).",
        inputFormat: "First line N. Second line N integers (parent array).",
        outputFormat: "Print tree height.",
        constraints: "1 <= N <= 1000",
        explanation: "Build tree from parent array. For each node, compute depth by traversing up to root. Height = max depth.",
        makeCase: (seed) => {
            const next = lcg(seed + 430);
            const n = randInt(next, 5, 12);
            const parent = Array(n).fill(0);
            parent[0] = -1;
            for (let i = 1; i < n; i++) {
                parent[i] = randInt(next, 0, i - 1);
            }
            const depths = Array(n).fill(0);
            for (let i = 0; i < n; i++) {
                let node = i;
                let d = 0;
                while (parent[node] !== -1) {
                    node = parent[node];
                    d++;
                }
                depths[i] = d;
            }
            const height = Math.max(...depths);
            return { input: `${n}\n${parent.join(" ")}`, output: `${height}` };
        }
    },
    {
        key: "ds-hash-table",
        title: "Hash Table Implementation",
        tags: ["Data Structures", "Hashing"],
        statement: "Implement a simple hash table of size 10 using modulo hashing. Read N integers, insert each using hash(key) = key % 10. For collisions, use linear probing. After all insertions, print the hash table as 10 values (empty slots as -1).",
        inputFormat: "First line N. Second line N integers.",
        outputFormat: "Print 10 space-separated values representing the hash table.",
        constraints: "1 <= N <= 10",
        explanation: "Compute hash = key % 10. If slot is taken, probe the next slot circularly. Track empty slots with -1.",
        makeCase: (seed) => {
            const next = lcg(seed + 440);
            const n = randInt(next, 3, 8);
            const arr = makeArray(seed + 441, n, 5, 95);
            const table = Array(10).fill(-1);
            for (const key of arr) {
                let idx = key % 10;
                while (table[idx] !== -1)
                    idx = (idx + 1) % 10;
                table[idx] = key;
            }
            return { input: `${n}\n${arr.join(" ")}`, output: table.join(" ") };
        }
    },
    {
        key: "ds-bst-search",
        title: "BST Search Operation",
        tags: ["Data Structures", "BST"],
        statement: "Given BST nodes inserted in order, read the insertion sequence and a query value. Print 'FOUND' if the value exists in the BST, else 'NOT FOUND'.",
        inputFormat: "First line N. Second line N integers (insertion order). Third line: query value.",
        outputFormat: "FOUND or NOT FOUND.",
        constraints: "1 <= N <= 100",
        explanation: "Build BST by inserting nodes. Then search: go left if query < node, right if query > node.",
        makeCase: (seed) => {
            const n = 5 + (seed % 5);
            const arr = makeArray(seed + 450, n, 1, 50);
            const uniqueArr = [...new Set(arr)];
            const queryIdx = seed % (uniqueArr.length + 2);
            const query = queryIdx < uniqueArr.length ? uniqueArr[queryIdx] : 99;
            const found = uniqueArr.includes(query);
            return { input: `${uniqueArr.length}\n${uniqueArr.join(" ")}\n${query}`, output: found ? "FOUND" : "NOT FOUND" };
        }
    }
];
const DIFFICULTY_SEQUENCE = [
    Difficulty.EASY,
    Difficulty.MEDIUM,
    Difficulty.HARD,
    Difficulty.MEDIUM,
    Difficulty.HARD
];
async function seedUsers() {
    const adminPass = await bcrypt.hash("admin123", 10);
    await prisma.user.upsert({
        where: { email: "admin@coding.local" },
        update: {},
        create: {
            name: "Portal Admin",
            email: "admin@coding.local",
            passwordHash: adminPass,
            role: Role.ADMIN
        }
    });
}
function buildProblems() {
    const allProblems = [];
    for (const template of templates) {
        // Determine supported languages based on problem tags
        let langs;
        const tagsLower = template.tags.map(t => t.toLowerCase());
        if (tagsLower.includes("html")) {
            langs = [Language.HTML];
        }
        else if (tagsLower.includes("css")) {
            langs = [Language.CSS];
        }
        else if (tagsLower.includes("javascript")) {
            langs = [Language.JAVASCRIPT, Language.PYTHON, Language.JAVA];
        }
        else if (tagsLower.includes("dbms") || tagsLower.includes("sql") || tagsLower.includes("normalization") || tagsLower.includes("er model")) {
            langs = [Language.PYTHON, Language.JAVASCRIPT];
        }
        else {
            langs = [Language.C, Language.CPP, Language.PYTHON, Language.JAVA, Language.JAVASCRIPT];
        }
        // Build language-specific starter codes
        const langStarterCodes = {};
        for (const lang of langs) {
            langStarterCodes[lang] = starterCodes[lang] || "";
        }
        for (let variant = 1; variant <= 5; variant++) {
            const baseSeed = variant * 1000 + template.key.length * 37;
            const c1 = template.makeCase(baseSeed + 1);
            const c2 = template.makeCase(baseSeed + 2);
            const c3 = template.makeCase(baseSeed + 3);
            allProblems.push({
                slug: `${template.key}-v${variant}`,
                title: `${template.title} (${variant})`,
                difficulty: DIFFICULTY_SEQUENCE[variant - 1],
                tags: template.tags,
                supportedLanguages: langs,
                statement: template.statement,
                inputFormat: template.inputFormat,
                outputFormat: template.outputFormat,
                constraints: template.constraints,
                sampleInput: c1.input,
                sampleOutput: c1.output,
                explanation: template.explanation,
                starterCodes: langStarterCodes,
                timeLimitMs: 2000,
                memoryLimitMb: 256,
                testCases: [
                    { input: c1.input, output: c1.output, isHidden: false },
                    { input: c2.input, output: c2.output, isHidden: false },
                    { input: c3.input, output: c3.output, isHidden: true }
                ]
            });
        }
    }
    return allProblems;
}
async function seedProblemsAndJourneys() {
    await prisma.journeyProblem.deleteMany();
    await prisma.journey.deleteMany();
    await prisma.userSolvedProblem.deleteMany();
    await prisma.submission.deleteMany();
    await prisma.testCase.deleteMany();
    await prisma.problem.deleteMany();
    const problemSeeds = buildProblems();
    for (const p of problemSeeds) {
        await prisma.problem.create({
            data: {
                slug: p.slug,
                title: p.title,
                difficulty: p.difficulty,
                tags: p.tags,
                supportedLanguages: p.supportedLanguages,
                statement: p.statement,
                inputFormat: p.inputFormat,
                outputFormat: p.outputFormat,
                constraints: p.constraints,
                sampleInput: p.sampleInput,
                sampleOutput: p.sampleOutput,
                explanation: p.explanation,
                starterCodes: p.starterCodes,
                timeLimitMs: p.timeLimitMs,
                memoryLimitMb: p.memoryLimitMb,
                testCases: {
                    create: p.testCases
                }
            }
        });
    }
    const allProblems = await prisma.problem.findMany({ orderBy: { title: "asc" } });
    const hasTag = (problemTags, tag) => Array.isArray(problemTags) && problemTags.some((t) => t.toLowerCase() === tag.toLowerCase());
    const arraysBasics = allProblems.filter((p) => hasTag(p.tags, "Arrays")).slice(0, 10);
    const stringsBasics = allProblems.filter((p) => hasTag(p.tags, "Strings")).slice(0, 10);
    const dpTrack = allProblems.filter((p) => hasTag(p.tags, "DP")).slice(0, 10);
    const htmlTrack = allProblems.filter((p) => hasTag(p.tags, "HTML")).slice(0, 10);
    const cssTrack = allProblems.filter((p) => hasTag(p.tags, "CSS")).slice(0, 10);
    const jsTrack = allProblems.filter((p) => hasTag(p.tags, "JavaScript")).slice(0, 10);
    const javaTrack = allProblems.filter((p) => hasTag(p.tags, "Java")).slice(0, 10);
    const dbmsTrack = allProblems.filter((p) => hasTag(p.tags, "DBMS")).slice(0, 10);
    const dsTrack = allProblems.filter((p) => hasTag(p.tags, "Data Structures")).slice(0, 10);
    const journeys = [
        {
            slug: "arrays-basics",
            title: "Arrays Basics",
            description: "Master core array techniques and scanning patterns.",
            problems: arraysBasics
        },
        {
            slug: "strings-basics",
            title: "Strings Basics",
            description: "Build confidence in string processing fundamentals.",
            problems: stringsBasics
        },
        {
            slug: "dynamic-programming-1",
            title: "Dynamic Programming 1",
            description: "Learn memoization and tabulation through starter DP tasks.",
            problems: dpTrack
        },
        {
            slug: "html-fundamentals",
            title: "HTML Fundamentals",
            description: "Learn HTML5 structure, forms, tables, and semantic elements.",
            problems: htmlTrack
        },
        {
            slug: "css-styling-basics",
            title: "CSS Styling & Layout",
            description: "Master CSS selectors, Flexbox, Grid, responsive design, and animations.",
            problems: cssTrack
        },
        {
            slug: "javascript-essentials",
            title: "JavaScript Essentials",
            description: "Practice JS variables, arrays, strings, objects, and async patterns.",
            problems: jsTrack
        },
        {
            slug: "java-oop-deep-dive",
            title: "Java OOP Deep Dive",
            description: "Explore Java class design, inheritance, collections, and exception handling.",
            problems: javaTrack
        },
        {
            slug: "dbms-sql-fundamentals",
            title: "DBMS & SQL Fundamentals",
            description: "Practice SQL queries, joins, subqueries, normalization, and ER modeling.",
            problems: dbmsTrack
        },
        {
            slug: "data-structures-core",
            title: "Data Structures Core",
            description: "Implement and work with linked lists, stacks, queues, trees, BSTs, and hash tables.",
            problems: dsTrack
        }
    ];
    for (const j of journeys) {
        await prisma.journey.create({
            data: {
                slug: j.slug,
                title: j.title,
                description: j.description,
                problems: {
                    create: j.problems.map((p, idx) => ({ problemId: p.id, orderIndex: idx + 1 }))
                }
            }
        });
    }
    console.log(`Seeded ${problemSeeds.length} problems.`);
}
async function main() {
    await seedUsers();
    await seedProblemsAndJourneys();
}
main()
    .then(async () => {
    await prisma.$disconnect();
    console.log("Seed complete");
})
    .catch(async (e) => {
    console.error(e);
    await prisma.$disconnect();
    process.exit(1);
});
