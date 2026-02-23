export const COVER_LETTER_TEMPLATES = {
  professional: (jobTitle: string, company: string) =>
    `Dear Hiring Manager,

I am writing to express my strong interest in the ${jobTitle} role at ${company}. With my background and experience, I am confident in my ability to make a meaningful contribution to your team.

[2–3 sentences about your most relevant experience and achievements that directly relate to this role.]

I am excited about the opportunity to bring my skills to ${company} and contribute to your team's continued success. I would welcome the chance to discuss how my background aligns with your needs.

Thank you for your time and consideration.

Sincerely,
[Your Name]`,

  creative: (jobTitle: string, company: string) =>
    `Hi there,

[Start with a brief, compelling story or surprising fact that connects your background to the ${jobTitle} role — something that makes you memorable.]

That experience — and others like it — led me here. ${company}'s work caught my attention because [one specific reason you're drawn to this company or team].

I'd love to bring that same energy and perspective to your team. Looking forward to connecting.

[Your Name]`,

  brief: (jobTitle: string, _company: string) =>
    `I am applying for the ${jobTitle} position because [one clear, specific reason].

My top three relevant strengths:
1. [Strength 1 — with a brief example]
2. [Strength 2 — with a brief example]
3. [Strength 3 — with a brief example]

Available to start [date]. Looking forward to your reply.

[Your Name]`,
} as const

export type TemplateName = keyof typeof COVER_LETTER_TEMPLATES
