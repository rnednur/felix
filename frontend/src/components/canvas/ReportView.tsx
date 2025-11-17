import { Download, FileText, Printer } from 'lucide-react'

interface ReportViewProps {
  report: any
}

export function ReportView({ report }: ReportViewProps) {
  const handleDownloadPDF = () => {
    // Use browser's print to PDF functionality
    // This is more reliable than generating HTML
    window.print()
  }

  const handlePrint = () => {
    window.print()
  }

  if (!report) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center text-gray-500">
          <p className="text-lg font-medium">No report available</p>
          <p className="text-sm mt-2">Run a Deep Research analysis to generate a report</p>
        </div>
      </div>
    )
  }

  return (
    <>
      {/* Print-specific styles */}
      <style>{`
        @media print {
          @page {
            size: A4;
            margin: 1.5cm;
          }

          /* Hide everything except report */
          body * {
            visibility: hidden;
          }

          #report-content,
          #report-content * {
            visibility: visible;
          }

          #report-content {
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
            max-width: 100% !important;
            padding: 0 !important;
            margin: 0 !important;
          }

          body {
            print-color-adjust: exact;
            -webkit-print-color-adjust: exact;
          }

          .no-print {
            display: none !important;
          }

          /* Page break control */
          details {
            page-break-inside: avoid;
          }

          summary {
            cursor: default;
            page-break-inside: avoid;
          }

          details[open] summary ~ * {
            display: block;
          }

          h1, h2, h3 {
            page-break-after: avoid;
          }

          img {
            page-break-inside: avoid;
            max-width: 100%;
          }

          .visualization-container {
            page-break-inside: avoid;
          }
        }
      `}</style>
      <div className="h-full overflow-auto bg-white">
      {/* Download Actions Bar */}
      <div className="sticky top-0 z-10 bg-white border-b border-gray-200 px-8 py-4 no-print">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <FileText className="h-4 w-4" />
            <span>Deep Research Report</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handlePrint}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <Printer className="h-4 w-4" />
              Print
            </button>
            <button
              onClick={handleDownloadPDF}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg hover:from-blue-700 hover:to-purple-700 transition-colors shadow-sm"
            >
              <Download className="h-4 w-4" />
              Download PDF
            </button>
          </div>
        </div>
      </div>

      <div id="report-content" className="max-w-4xl mx-auto p-8 print-container">
        {/* Header */}
        <div className="mb-8 pb-6 border-b border-gray-200">
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
            <span>Deep Research Report</span>
            <span>•</span>
            <span>{new Date().toLocaleDateString()}</span>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            {report.main_question}
          </h1>
          <div className="flex items-center gap-4 text-sm text-gray-600">
            <span>⏱️ {report.execution_time_seconds.toFixed(1)}s</span>
            <span>📊 {report.sub_questions_count} analyses</span>
            {report.visualizations?.length > 0 && (
              <span>📈 {report.visualizations.length} visualizations</span>
            )}
          </div>
        </div>

        {/* Executive Summary */}
        <section className="mb-10">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <span className="w-1 h-6 bg-blue-600 rounded"></span>
            Executive Summary
          </h2>
          <div className="bg-blue-50 border-l-4 border-blue-600 p-6 rounded-r-lg">
            <p className="text-gray-800 leading-relaxed text-lg">
              {report.direct_answer}
            </p>
          </div>
        </section>

        {/* Key Findings */}
        {report.key_findings?.length > 0 && (
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <span className="w-1 h-6 bg-green-600 rounded"></span>
              Key Findings
            </h2>
            <div className="space-y-3">
              {report.key_findings.map((finding: string, idx: number) => (
                <div key={idx} className="flex gap-3 items-start">
                  <div className="flex-shrink-0 w-6 h-6 bg-green-100 text-green-700 rounded-full flex items-center justify-center text-sm font-semibold mt-0.5">
                    {idx + 1}
                  </div>
                  <p className="text-gray-700 leading-relaxed flex-1 pt-0.5">
                    {finding}
                  </p>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Visualizations */}
        {report.visualizations?.length > 0 && (
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <span className="w-1 h-6 bg-purple-600 rounded"></span>
              Visualizations
            </h2>
            <div className="space-y-6">
              {report.visualizations.map((viz: any, idx: number) => (
                <div key={idx} className="bg-gray-50 border border-gray-200 rounded-lg p-6">
                  <p className="text-sm font-medium text-gray-700 mb-4">
                    Figure {idx + 1}: {viz.caption}
                  </p>
                  <div className="bg-white rounded-lg p-4 border border-gray-100">
                    <img
                      src={`data:${viz.format === 'png' ? 'image/png' : 'image/jpeg'};base64,${viz.data}`}
                      alt={viz.caption}
                      className="w-full h-auto rounded"
                    />
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Data Coverage */}
        {report.data_coverage && (
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <span className="w-1 h-6 bg-yellow-600 rounded"></span>
              Data Coverage & Limitations
            </h2>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="text-2xl font-bold text-green-700 mb-1">
                  {report.data_coverage.questions_answered || 0}
                </div>
                <div className="text-sm text-green-600">Questions Answered</div>
              </div>
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <div className="text-2xl font-bold text-gray-700 mb-1">
                  {report.data_coverage.total_questions || 0}
                </div>
                <div className="text-sm text-gray-600">Total Analyses</div>
              </div>
            </div>
            {report.data_coverage.gaps?.length > 0 && (
              <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded-r-lg">
                <p className="text-sm font-medium text-yellow-800 mb-2">⚠️ Data Gaps Identified</p>
                <ul className="text-sm text-yellow-700 space-y-1 list-disc list-inside">
                  {report.data_coverage.gaps.map((gap: string, idx: number) => (
                    <li key={idx}>{gap}</li>
                  ))}
                </ul>
              </div>
            )}
          </section>
        )}

        {/* Research Details - Show all the work */}
        {report.supporting_details && Array.isArray(report.supporting_details) && report.supporting_details.length > 0 && (
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <span className="w-1 h-6 bg-gray-600 rounded"></span>
              Research Details
            </h2>
            <p className="text-sm text-gray-600 mb-4">
              Below are all the analyses performed to answer your question, including sub-questions, queries, code, and results.
            </p>
            <div className="space-y-4">
              {report.supporting_details.map((detail: any, idx: number) => (
                <details key={idx} className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                  <summary className="px-5 py-4 cursor-pointer hover:bg-gray-50 transition-colors">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className="flex-shrink-0 w-7 h-7 bg-gray-100 text-gray-700 rounded-full flex items-center justify-center text-sm font-semibold">
                          {idx + 1}
                        </span>
                        <div>
                          <p className="font-medium text-gray-900">{detail.question}</p>
                          <div className="flex items-center gap-2 mt-1">
                            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                              detail.method === 'sql' ? 'bg-blue-100 text-blue-700' :
                              detail.method === 'python' ? 'bg-purple-100 text-purple-700' :
                              'bg-gray-100 text-gray-700'
                            }`}>
                              {detail.method?.toUpperCase() || 'N/A'}
                            </span>
                            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                              detail.success ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                            }`}>
                              {detail.success ? '✓ Success' : '✗ Failed'}
                            </span>
                          </div>
                        </div>
                      </div>
                      <svg className="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                  </summary>

                  <div className="px-5 py-4 bg-gray-50 border-t border-gray-200 space-y-4">
                    {/* SQL Query */}
                    {detail.method === 'sql' && detail.data?.sql && (
                      <div>
                        <p className="text-xs font-semibold text-gray-700 mb-2 uppercase tracking-wide">SQL Query</p>
                        <div className="bg-gray-900 rounded-lg overflow-hidden">
                          <pre className="p-4 text-sm text-gray-100 overflow-x-auto">
                            <code>{detail.data.sql}</code>
                          </pre>
                        </div>
                      </div>
                    )}

                    {/* Python Code */}
                    {detail.method === 'python' && detail.data?.code && (
                      <div>
                        {detail.success && (detail.data.preview || detail.data.summary) ? (
                          <details className="group">
                            <summary className="text-xs font-semibold text-gray-700 mb-2 uppercase tracking-wide cursor-pointer hover:text-gray-900 flex items-center gap-2">
                              <svg className="w-4 h-4 text-gray-400 group-open:rotate-90 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                              </svg>
                              Python Code (click to expand)
                            </summary>
                            <div className="bg-gray-900 rounded-lg overflow-hidden mt-2">
                              <pre className="p-4 text-sm text-gray-100 overflow-x-auto">
                                <code>{detail.data.code || 'Code not available'}</code>
                              </pre>
                            </div>
                          </details>
                        ) : (
                          <>
                            <p className="text-xs font-semibold text-gray-700 mb-2 uppercase tracking-wide">Python Code</p>
                            <div className="bg-gray-900 rounded-lg overflow-hidden">
                              <pre className="p-4 text-sm text-gray-100 overflow-x-auto">
                                <code>{detail.data.code || 'Code not available'}</code>
                              </pre>
                            </div>
                          </>
                        )}
                      </div>
                    )}

                    {/* Results */}
                    {detail.success && detail.data && (
                      <div>
                        <p className="text-xs font-semibold text-gray-700 mb-2 uppercase tracking-wide">Results</p>
                        {detail.data.preview && Array.isArray(detail.data.preview) && detail.data.preview.length > 0 ? (
                          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                            <div className="overflow-x-auto">
                              <table className="min-w-full divide-y divide-gray-200 text-sm">
                                <thead className="bg-gray-50">
                                  <tr>
                                    {Object.keys(detail.data.preview[0]).map((key: string) => (
                                      <th key={key} className="px-4 py-2 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                                        {key}
                                      </th>
                                    ))}
                                  </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                  {detail.data.preview.slice(0, 5).map((row: any, rowIdx: number) => (
                                    <tr key={rowIdx} className="hover:bg-gray-50">
                                      {Object.values(row).map((val: any, colIdx: number) => (
                                        <td key={colIdx} className="px-4 py-2 whitespace-nowrap text-gray-900">
                                          {val !== null && val !== undefined ? String(val) : '-'}
                                        </td>
                                      ))}
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                            {detail.data.rows > 5 && (
                              <div className="px-4 py-2 bg-gray-50 border-t border-gray-200 text-xs text-gray-600">
                                Showing 5 of {detail.data.rows} rows
                              </div>
                            )}
                          </div>
                        ) : detail.data.summary ? (
                          <div className="bg-white border border-gray-200 rounded-lg p-4">
                            <p className="text-sm text-gray-700">{detail.data.summary}</p>
                          </div>
                        ) : (
                          <div className="bg-white border border-gray-200 rounded-lg p-4">
                            <pre className="text-xs text-gray-700 overflow-x-auto">
                              {JSON.stringify(detail.data, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Error */}
                    {!detail.success && detail.error && (
                      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                        <p className="text-xs font-semibold text-red-700 mb-1 uppercase tracking-wide">Error</p>
                        <p className="text-sm text-red-600">{detail.error}</p>
                      </div>
                    )}
                  </div>
                </details>
              ))}
            </div>
          </section>
        )}

        {/* Follow-up Questions */}
        {report.follow_up_questions?.length > 0 && (
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <span className="w-1 h-6 bg-indigo-600 rounded"></span>
              Recommended Next Steps
            </h2>
            <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-6">
              <p className="text-sm text-indigo-700 mb-4">
                Consider exploring these questions for deeper insights:
              </p>
              <div className="space-y-2">
                {report.follow_up_questions.map((question: string, idx: number) => (
                  <div key={idx} className="flex gap-2 items-start">
                    <span className="text-indigo-600 font-semibold">{idx + 1}.</span>
                    <p className="text-gray-700">{question}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}

        {/* Footer */}
        <div className="mt-12 pt-6 border-t border-gray-200 text-center text-sm text-gray-500">
          <div className="flex items-center justify-center gap-2 mb-2">
            <svg className="h-4 w-4 text-purple-600" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2c-1.1 0-2 .9-2 2v2c0 1.1.9 2 2 2s2-.9 2-2V4c0-1.1-.9-2-2-2zm-9 9c0-1.1.9-2 2-2h2c1.1 0 2 .9 2 2s-.9 2-2 2H5c-1.1 0-2-.9-2-2zm14 0c0-1.1.9-2 2-2h2c1.1 0 2 .9 2 2s-.9 2-2 2h-2c-1.1 0-2-.9-2-2zM12 16c-2.2 0-4 1.8-4 4v2h8v-2c0-2.2-1.8-4-4-4zm-6.8-3.2l-1.4-1.4c-.8-.8-.8-2 0-2.8.8-.8 2-.8 2.8 0l1.4 1.4c.8.8.8 2 0 2.8-.8.8-2 .8-2.8 0zm13.6 0c-.8.8-2 .8-2.8 0-.8-.8-.8-2 0-2.8l1.4-1.4c.8-.8 2-.8 2.8 0 .8.8.8 2 0 2.8l-1.4 1.4zM12 13c.6 0 1 .4 1 1s-.4 1-1 1-1-.4-1-1 .4-1 1-1z"/>
            </svg>
            <p className="font-medium text-gray-700">Generated by Felix • Deep Research Engine</p>
          </div>
          <p className="mt-1">Report ID: {report.research_id}</p>
        </div>
      </div>
    </div>
    </>
  )
}
