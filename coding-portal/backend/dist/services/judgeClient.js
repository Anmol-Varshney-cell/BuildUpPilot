import axios from "axios";
import { env } from "../config/env.js";
export function toJudgeCases(testCases) {
    return testCases.map((t) => ({
        id: t.id,
        input: t.input,
        expectedOutput: t.output,
        isHidden: t.isHidden
    }));
}
export async function executeInJudge(payload) {
    const response = await axios.post(`${env.judgeUrl}/execute`, payload, {
        timeout: 120000
    });
    return response.data;
}
