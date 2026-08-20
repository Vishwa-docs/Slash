import { Component, type ErrorInfo, type ReactNode } from "react";

interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<{ children: ReactNode }, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("[slash] render error boundary", error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="card" style={{ margin: 24 }}>
          <div className="card-hd">
            <span className="tag abstain">rendering error</span>
          </div>
          <div className="card-body">
            <p className="answer-text">
              One panel failed to render — the rest of the console is fine. Reload the
              page to continue (nothing was lost; the graph is queryable again instantly).
            </p>
            <p className="reason" style={{ marginTop: 10 }}>
              {String(this.state.error)}
            </p>
            <button
              className="btn-scan"
              onClick={() => window.location.reload()}
              style={{ marginTop: 12 }}
            >
              reload console
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}