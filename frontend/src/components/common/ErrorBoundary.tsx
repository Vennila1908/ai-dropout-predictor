import { Component, type ErrorInfo, type ReactNode } from 'react';

interface Props { children: ReactNode }
interface State { hasError: boolean; message?: string }

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, message: error.message };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error('ErrorBoundary caught:', error, info);
  }

  reset = () => this.setState({ hasError: false, message: undefined });

  render() {
    if (!this.state.hasError) return this.props.children;
    return (
      <div className="flex min-h-[60vh] items-center justify-center p-6">
        <div className="card max-w-lg p-6 text-center">
          <h2 className="mb-2 text-xl font-semibold">Something broke</h2>
          <p className="mb-4 text-sm text-ink-muted">{this.state.message ?? 'An unexpected error occurred.'}</p>
          <button className="btn-primary" onClick={this.reset}>Try again</button>
        </div>
      </div>
    );
  }
}
