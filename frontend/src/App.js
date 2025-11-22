// src/App.js
import React, { useState } from "react";
import {
  Container,
  Row,
  Col,
  Card,
  Button,
  Form,
  Spinner,
  Alert,
  Badge,
} from "react-bootstrap";
import Dashboard from "./Dashboard";

const API_BASE = process.env.REACT_APP_API_BASE || "http://127.0.0.1:8000";

function App() {
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const handleFileChange = (event) => {
    setFile(event.target.files[0] || null);
    setError("");
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!file) {
      setError("Please select a CSV file before uploading.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setIsUploading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(`${API_BASE}/analyze`, {
        method: "POST",
        body: formData,
      });

      let data = {};
      try {
        data = await response.json();
      } catch {
        // ignore JSON parse errors; fall back to generic message
      }

      if (!response.ok) {
        const rawDetail = data?.detail ?? data;
        let message = "Failed to analyze file. Please try again.";

        if (typeof rawDetail === "string") {
          message = rawDetail;
        } else if (rawDetail && typeof rawDetail === "object") {
          const parts = [
            rawDetail.message,
            rawDetail.error_type ? `(${rawDetail.error_type})` : "",
            rawDetail.error ? `: ${rawDetail.error}` : "",
          ].filter(Boolean);
          if (parts.length) {
            message = parts.join(" ");
          }
        }

        throw new Error(message);
      }

      setResult(data);
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error(err);
      setError(err.message || "Something went wrong while calling the API.");
    } finally {
      setIsUploading(false);
    }
  };

  // Build figures object with full URLs for Dashboard
  const figuresWithBase =
    result?.figures != null
      ? Object.fromEntries(
          Object.entries(result.figures).map(([key, url]) => [
            key,
            `${API_BASE}${url}`,
          ]),
        )
      : null;

  return (
    <div className="app-root">
      <div className="app-overlay" />

      {/* Top navbar-style header */}
      <header className="app-header px-3 px-md-5 py-3">
        <div className="d-flex align-items-center justify-content-between">
          <div>
            <h1 className="fw-bold mb-0 text-white app-title">
              TechSophy Finance Insights
            </h1>
            <p className="text-light-50 mb-0 small">
              ML-powered personal finance dashboard
            </p>
          </div>
          <div className="d-flex align-items-center gap-2">
            <Badge bg="info" text="dark" className="fs-6">
              Beta
            </Badge>
            <span className="text-light-50 small d-none d-md-inline">
              v1.0 • FastAPI + React + ML
            </span>
          </div>
        </div>
      </header>

      <Container className="py-4 position-relative">
        <Row className="g-4">
          {/* Upload card */}
          <Col md={4}>
            <Card className="shadow-lg card-glass card-upload">
              <Card.Body>
                <Card.Title>Upload Transactions</Card.Title>
                <Card.Text className="text-muted small">
                  Upload a CSV exported from your bank or wallet app. We’ll
                  compute category-wise spend, trends, anomalies, and
                  recommendations.
                  <br />
                  <span className="text-light-50">
                    Expected columns:{" "}
                    <code>
                      Transaction Date, Description, Amount, Transaction_Type
                    </code>
                    .
                  </span>
                </Card.Text>

                {error && (
                  <Alert
                    variant="danger"
                    onClose={() => setError("")}
                    dismissible
                    className="mt-3"
                  >
                    <strong>Analysis failed: </strong>
                    {error}
                  </Alert>
                )}

                <Form onSubmit={handleSubmit} className="mt-3">
                  <Form.Group controlId="file" className="mb-3">
                    <Form.Label className="fw-semibold">
                      Select CSV file
                    </Form.Label>
                    <Form.Control
                      type="file"
                      accept=".csv"
                      onChange={handleFileChange}
                    />
                    {file && (
                      <small className="text-muted d-block mt-1">
                        Selected: {file.name}
                      </small>
                    )}
                  </Form.Group>

                  <Button
                    type="submit"
                    variant="primary"
                    disabled={isUploading}
                    className="w-100 btn-elevated"
                  >
                    {isUploading ? (
                      <>
                        <Spinner
                          animation="border"
                          size="sm"
                          className="me-2"
                        />
                        Analyzing your spending…
                      </>
                    ) : (
                      "Analyze my spending"
                    )}
                  </Button>
                </Form>

                {result && (
                  <div className="mt-3 small text-muted">
                    <span className="d-block fw-semibold mb-1">Run ID</span>
                    <code className="text-wrap d-block">{result.run_id}</code>
                  </div>
                )}
              </Card.Body>
            </Card>
          </Col>

          {/* Dashboard area */}
          <Col md={8}>
            {!result && !isUploading && (
              <Card className="shadow-lg h-100 card-glass card-empty">
                <Card.Body className="text-center d-flex flex-column justify-content-center">
                  <h4 className="mb-3">No analysis yet</h4>
                  <p className="text-muted mb-0">
                    Upload a CSV on the left to generate your personalized
                    finance dashboard with charts and recommendations.
                  </p>
                </Card.Body>
              </Card>
            )}

            {isUploading && (
              <Card className="shadow-lg h-100 card-glass card-loading">
                <Card.Body className="text-center d-flex flex-column justify-content-center">
                  <Spinner animation="border" className="mb-3" />
                  <h4>Crunching the numbers…</h4>
                  <p className="text-muted mb-0">
                    We’re clustering your spending, detecting anomalies, and
                    preparing your dashboard.
                  </p>
                </Card.Body>
              </Card>
            )}

            {result && !isUploading && (
              <Dashboard
                summary={result.summary}
                recommendations={result.recommendations || []}
                figures={figuresWithBase || {}}
                isAnalyzing={isUploading}
                lastRunId={result.run_id}
              />
            )}
          </Col>
        </Row>
      </Container>
    </div>
  );
}

export default App;
