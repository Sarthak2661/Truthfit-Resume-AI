import { ErrorPanel } from "../../../components/ErrorPanel";
import { getProviders } from "../../../lib/api";

export default async function ProvidersPage() {
  try {
    const { providers } = await getProviders();

    return (
      <section className="section">
        <div className="section-label">Model settings</div>
        <h1>Analysis models</h1>
        <p className="muted">Choose the model family and default model used for live resume reviews.</p>

        <div className="section grid two">
          {providers.map((provider) => (
            <div className="card" key={provider.name}>
              <h3>{provider.name}</h3>
              <p>
                <span className="pill">Default: {provider.default_model}</span>
              </p>
              <table className="table">
                <thead>
                  <tr>
                    <th>Available models</th>
                  </tr>
                </thead>
                <tbody>
                  {provider.models.map((model) => (
                    <tr key={model}>
                      <td>{model}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </div>
      </section>
    );
  } catch (error) {
    return <ErrorPanel message={error instanceof Error ? error.message : "Unknown API error"} />;
  }
}
