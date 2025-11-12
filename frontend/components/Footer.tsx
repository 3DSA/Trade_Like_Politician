export function Footer() {
  return (
    <footer className="mt-auto border-t border-neutral-200 dark:border-slate-800 bg-white dark:bg-slate-950 transition-colors duration-300">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="text-sm text-neutral-600 dark:text-slate-400">
            <p className="mb-2">
              Data sourced from official{" "}
              <a
                href="https://efdsearch.senate.gov/search/"
                target="_blank"
                rel="noopener noreferrer"
                className="font-medium text-neutral-900 dark:text-slate-100 hover:underline transition-colors"
              >
                U.S. Senate eFD
              </a>{" "}
              financial disclosures
            </p>
            <p className="text-xs text-neutral-500 dark:text-slate-500">
              Last updated: {new Date().toLocaleDateString("en-US", {
                month: "long",
                day: "numeric",
                year: "numeric",
              })}
            </p>
          </div>

          <div className="flex items-center gap-6 text-sm text-neutral-600 dark:text-slate-400">
            <a
              href="https://github.com/yourusername/trade-like-politician"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-neutral-900 dark:hover:text-slate-100 transition-colors"
            >
              GitHub
            </a>
            <a
              href="https://www.congress.gov/"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-neutral-900 dark:hover:text-slate-100 transition-colors"
            >
              Congress.gov
            </a>
          </div>
        </div>

        <div className="mt-6 pt-6 border-t border-neutral-100 dark:border-slate-800">
          <p className="text-xs text-neutral-500 dark:text-slate-500">
            © {new Date().getFullYear()} Senate Trading Tracker. For informational purposes only.
            Not investment advice. Data may contain errors or delays.
          </p>
        </div>
      </div>
    </footer>
  );
}
