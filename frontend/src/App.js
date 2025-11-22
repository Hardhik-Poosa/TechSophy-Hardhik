// src/App.js
import React, { useState } from 'react';
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
  Modal,
  ProgressBar,
} from 'react-bootstrap';

const API_BASE = process.env.REACT_APP_API_BASE || 'http://127.0.0.1:8000';

function App() {
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [showChartModal, setShowChartModal] = useState(false);
  const [activeChart, setActiveChart] = useState(null);

  const handleFileChange = (event) => {
    setFile(event.target.files[0] || null);
    setError('');
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!file) {
      setError('Please select a CSV file before uploading.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    setIsUploading(true);
    setError('');
    setResult(null);

    try {
      const response = await fetch(`${API_BASE}/analyze`, {
        method: 'POST',
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
        let message = 'Failed to analyze file. Please try again.';

        if (typeof rawDetail === 'string') {
          message = rawDetail;
        } else if (rawDetail && typeof rawDetail === 'object') {
          const parts = [
            rawDetail.message,
            rawDetail.error_type ? `(${rawDetail.error_type})` : '',
            rawDetail.error ? `: ${rawDetail.error}` : '',
          ].filter(Boolean);
          if (parts.length) {
            message = parts.join(' ');
          }
        }

        throw new Error(message);
      }

      setResult(data);
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error(err);
      setError(err.message || 'Something went wrong while calling the API.');
    } finally {
      setIsUploading(false);
    }
  };

  const openChartModal = (chart) => {
    setActiveChart(chart);
    setShowChartModal(true);
  };

  const closeChartModal = () => {
    setShowChartModal(false);
    setActiveChart(null);
  };

  const renderSummaryCards = () => {
    if (!result) return null;

    const { summary } = result;
    const isNegativeCashFlow = summary.net_cash_flow < 0;

    const totalVolume =
      Math.abs(summary.total_spend) + Math.abs(summary.total_income);
    const spendRatio =
      totalVolume > 0
        ? Math.round((Math.abs(summary.total_spend) / totalVolume) * 100)
        : 0;

    return (
      <>
        <Row className="g-3 mb-3">
          <Col md={3} sm={6}>
            <Card className="shadow-sm h-100 card-glass card-hover">
              <Card.Body>
                <div className="d-flex justify-content-between align-items-center">
                  <Card.Title className="mb-0 small text-uppercase text-muted">
                    Total Spend
                  </Card.Title>
                  <span className="emoji-pill">💸</span>
                </div>
                <Card.Text className="fs-4 mt-2 text-danger fw-semibold">
                  ₹
                  {summary.total_spend.toLocaleString(undefined, {
                    maximumFractionDigits: 2,
                  })}
                </Card.Text>
              </Card.Body>
            </Card>
          </Col>
          <Col md={3} sm={6}>
            <Card className="shadow-sm h-100 card-glass card-hover">
              <Card.Body>
                <div className="d-flex justify-content-between align-items-center">
                  <Card.Title className="mb-0 small text-uppercase text-muted">
                    Total Income
                  </Card.Title>
                  <span className="emoji-pill">💰</span>
                </div>
                <Card.Text className="fs-4 mt-2 text-success fw-semibold">
                  ₹
                  {summary.total_income.toLocaleString(undefined, {
                    maximumFractionDigits: 2,
                  })}
                </Card.Text>
              </Card.Body>
            </Card>
          </Col>
          <Col md={3} sm={6}>
            <Card className="shadow-sm h-100 card-glass card-hover">
              <Card.Body>
                <div className="d-flex justify-content-between align-items-center">
                  <Card.Title className="mb-0 small text-uppercase text-muted">
                    Net Cash Flow
                  </Card.Title>
                  <span className="emoji-pill">
                    {isNegativeCashFlow ? '⚠️' : '✅'}
                  </span>
                </div>
                <Card.Text
                  className={`fs-4 mt-2 fw-semibold ${
                    isNegativeCashFlow ? 'text-danger' : 'text-success'
                  }`}
                >
                  {isNegativeCashFlow ? '▼ ' : '▲ '}
                  ₹
                  {summary.net_cash_flow.toLocaleString(undefined, {
                    maximumFractionDigits: 2,
                  })}
                </Card.Text>
              </Card.Body>
            </Card>
          </Col>
          <Col md={3} sm={6}>
            <Card className="shadow-sm h-100 card-glass card-hover">
              <Card.Body>
                <div className="d-flex justify-content-between align-items-center">
                  <Card.Title className="mb-0 small text-uppercase text-muted">
                    Transactions
                  </Card.Title>
                  <span className="emoji-pill">📊</span>
                </div>
                <Card.Text className="fs-4 mt-2 fw-semibold">
                  {summary.num_transactions.toLocaleString()}
                </Card.Text>
              </Card.Body>
            </Card>
          </Col>
        </Row>

        <Row>
          <Col md={6}>
            <Card className="shadow-sm card-glass mb-3">
              <Card.Body>
                <Card.Title className="small text-uppercase text-muted mb-2">
                  Spending vs Income
                </Card.Title>
                <div className="d-flex justify-content-between mb-1 small">
                  <span>Spending share</span>
                  <span>{spendRatio}% of total volume</span>
                </div>
                <ProgressBar
                  now={spendRatio}
                  label={`${spendRatio}%`}
                  variant={spendRatio > 70 ? 'danger' : 'success'}
                />
              </Card.Body>
            </Card>
          </Col>
        </Row>
      </>
    );
  };

  const renderRecommendations = () => {
    if (!result || !result.recommendations?.length) return null;

    return (
      <Card className="shadow-sm mt-3 card-glass">
        <Card.Body>
          <div className="d-flex justify-content-between align-items-center mb-2">
            <div>
              <Card.Title className="mb-0">Smart Recommendations</Card.Title>
              <small className="text-muted">
                Generated from your spending patterns and anomalies
              </small>
            </div>
            <Badge bg="primary" pill>
              {result.recommendations.length}
            </Badge>
          </div>
          <ul className="mb-0 fancy-list">
            {result.recommendations.map((rec, index) => (
              <li key={index} className="mb-2">
                {rec}
              </li>
            ))}
          </ul>
        </Card.Body>
      </Card>
    );
  };

  const renderCharts = () => {
    if (!result || !result.figures) return null;

    const { figures } = result;

    const chartConfigs = [
      {
        key: 'category_spending',
        title: 'Spending by Category',
        subtitle: 'Top categories where your money goes',
        accent: 'info',
      },
      {
        key: 'spending_trends',
        title: 'Spending Trends Over Time',
        subtitle: 'Month-over-month cash flow',
        accent: 'primary',
      },
      {
        key: 'anomaly_detection',
        title: 'Anomaly Detection',
        subtitle: 'Unusual or risky transactions',
        accent: 'warning',
      },
      {
        key: 'cluster_distribution',
        title: 'Cluster Distribution',
        subtitle: 'Behavioral spending clusters',
        accent: 'success',
      },
    ];

    const availableCharts = chartConfigs.filter((cfg) => figures[cfg.key]);

    if (!availableCharts.length) return null;

    return (
      <Row className="mt-4 g-4">
        {availableCharts.map((cfg) => {
          const url = figures[cfg.key];

          return (
            <Col md={6} key={cfg.key}>
              <Card
                className="shadow-sm h-100 card-glass card-hover chart-card"
                onClick={() => openChartModal({ ...cfg, url })}
              >
                <Card.Body>
                  <div className="d-flex justify-content-between align-items-center mb-2">
                    <div>
                      <Card.Title className="mb-0">{cfg.title}</Card.Title>
                      <small className="text-muted">{cfg.subtitle}</small>
                    </div>
                    <Badge bg={cfg.accent} pill>
                      View
                    </Badge>
                  </div>
                  <div className="text-center mt-3">
                    <img
                      src={`${API_BASE}${url}`}
                      alt={cfg.title}
                      className="img-fluid rounded chart-thumb"
                    />
                  </div>
                </Card.Body>
              </Card>
            </Col>
          );
        })}
      </Row>
    );
  };

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
                    Expected columns:{' '}
                    <code>
                      Transaction Date, Description, Amount, Transaction_Type
                    </code>
                    .
                  </span>
                </Card.Text>

                {error && (
                  <Alert
                    variant="danger"
                    onClose={() => setError('')}
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
                      'Analyze my spending'
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
              <>
                {renderSummaryCards()}
                {renderRecommendations()}
                {renderCharts()}
              </>
            )}
          </Col>
        </Row>
      </Container>

      {/* Full-screen chart modal */}
      <Modal
        show={showChartModal}
        onHide={closeChartModal}
        size="xl"
        centered
        contentClassName="chart-modal"
      >
        {activeChart && (
          <>
            <Modal.Header closeButton>
              <Modal.Title>{activeChart.title}</Modal.Title>
            </Modal.Header>
            <Modal.Body>
              <p className="text-muted small mb-3">{activeChart.subtitle}</p>
              <div className="text-center">
                <img
                  src={`${API_BASE}${activeChart.url}`}
                  alt={activeChart.title}
                  className="img-fluid rounded"
                  style={{ maxHeight: '80vh', objectFit: 'contain' }}
                />
              </div>
            </Modal.Body>
          </>
        )}
      </Modal>
    </div>
  );
}

export default App;
