const explanations = [
  ["Why it exists", "Bring a benefits request and its evidence together, so people can review it without chasing separate files."],
  ["Who it helps", "Reviewers check evidence, contact teams explain status, and employers see group trends, not individual records."],
  ["People make the decision", "Agents prepare checks and citations. A human must approve, decline or ask for more information."],
  ["How it connects", "Next.js talks to internal Python agents. Canadian AI, search and document reading help; private SQL keeps records."],
  ["What the AI does", "Microsoft Agent Framework powers case-bound chat. The model explains evidence and status; it never decides."],
  ["Where the IQs fit", "IQs are future options for enterprise knowledge and data. Today, we use Azure AI Search with synthetic sources."],
  ["How services stay protected", "Services use managed identities, not stored keys. The backend is internal and SQL uses a private connection."],
  ["Know the demo limits", "Anyone can switch demo views; this is not sign-in. No real member data, document uploads or external sends."],
] as const;

export function UseCaseGuide() {
  return <section className="use-case-guide" data-tour="use-case" aria-labelledby="use-case-title">
    <p className="eyebrow">THE PUBLIC SYNTHETIC SHOWCASE, SIMPLY EXPLAINED</p>
    <h2 id="use-case-title">Why this dashboard?</h2>
    <p>What it is for, how it fits together, and where people stay in control.</p>
    <div className="use-case-grid">{explanations.map(([title, explanation]) =>
      <article className="card use-case-card" key={title}><h3>{title}</h3><p>{explanation}</p></article>
    )}</div>
    <p className="small use-case-details">Local mode uses fixtures, not a live cloud connection.{" "}
      <a href="https://github.com/Rebecca-Shiney/benefits-iq/blob/main/README.md#architecture" target="_blank" rel="noreferrer">More architecture and safety details</a>.
    </p>
  </section>;
}
