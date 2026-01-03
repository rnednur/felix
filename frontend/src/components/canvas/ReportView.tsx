import { useState } from 'react'
import { Download, FileText, Printer, Presentation, Loader2 } from 'lucide-react'
import { useGeneratePresentation, downloadPresentationFromBase64 } from '@/hooks/usePresentation'
import { useToast } from '@/components/ui/toast'

interface ReportViewProps {
  report: any
}

export function ReportView({ report }: ReportViewProps) {
  const [pptTheme, setPptTheme] = useState<'professional' | 'modern' | 'corporate' | 'vibrant'>('professional')
  const [showThemeSelector, setShowThemeSelector] = useState(false)
  const generatePresentation = useGeneratePresentation()
  const { addToast } = useToast()

  const handleDownloadPDF = () => {
    // Use browser's print to PDF functionality
    // This is more reliable than generating HTML
    window.print()
  }

  const handlePrint = () => {
    window.print()
  }

  const handleGeneratePowerPoint = () => {
    setShowThemeSelector(!showThemeSelector)
  }

  const handleGenerateWithTheme = (theme: typeof pptTheme) => {
    generatePresentation.mutate(
      {
        research_result: report,
        theme: theme,
        include_verbose: !!report.methodology
      },
      {
        onSuccess: (data) => {
          addToast({
            title: 'PowerPoint Generated!',
            description: `Created ${data.file_name} (${(data.file_size / 1024).toFixed(0)} KB)`,
            type: 'success',
            duration: 5000
          })

          // Download the file
          downloadPresentationFromBase64(data.data, data.file_name)
          setShowThemeSelector(false)
        },
        onError: (error: any) => {
          addToast({
            title: 'Generation Failed',
            description: error.message || 'Failed to generate PowerPoint',
            type: 'error'
          })
        }
      }
    )
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
            <div className="relative">
              <button
                onClick={handleGeneratePowerPoint}
                disabled={generatePresentation.isPending}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-orange-600 to-red-600 rounded-lg hover:from-orange-700 hover:to-red-700 transition-colors shadow-sm disabled:opacity-50"
              >
                {generatePresentation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Presentation className="h-4 w-4" />
                    PowerPoint
                  </>
                )}
              </button>

              {showThemeSelector && !generatePresentation.isPending && (
                <div className="absolute top-full right-0 mt-2 bg-white border border-gray-200 rounded-lg shadow-lg p-3 min-w-[200px] z-20">
                  <div className="text-xs font-semibold text-gray-700 mb-2">Choose Theme:</div>
                  {(['professional', 'modern', 'corporate', 'vibrant'] as const).map((theme) => (
                    <button
                      key={theme}
                      onClick={() => handleGenerateWithTheme(theme)}
                      className="w-full text-left px-3 py-2 text-sm rounded hover:bg-gray-100 capitalize"
                    >
                      {theme}
                    </button>
                  ))}
                </div>
              )}
            </div>
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

        {/* Executive Summary - Enhanced for Verbose Mode */}
        <section className="mb-10">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <span className="w-1 h-6 bg-blue-600 rounded"></span>
            Executive Summary
          </h2>
          <div className="bg-blue-50 border-l-4 border-blue-600 p-6 rounded-r-lg">
            {report.executive_summary ? (
              <div className="prose prose-lg max-w-none">
                <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                  {report.executive_summary}
                </p>
              </div>
            ) : (
              <p className="text-gray-800 leading-relaxed text-lg">
                {report.direct_answer}
              </p>
            )}
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
                    {detail.method === 'sql' && (detail.code || detail.data?.sql) && (
                      <div>
                        <p className="text-xs font-semibold text-gray-700 mb-2 uppercase tracking-wide">SQL Query</p>
                        <div className="bg-gray-900 rounded-lg overflow-hidden">
                          <pre className="p-4 text-sm text-gray-100 overflow-x-auto max-h-96 overflow-y-auto">
                            <code>{detail.code || detail.data?.sql}</code>
                          </pre>
                        </div>
                      </div>
                    )}

                    {/* Python Code */}
                    {detail.method === 'python' && detail.code && (
                      <div>
                        {detail.success && (detail.data?.preview || detail.data?.summary) ? (
                          <details className="group">
                            <summary className="text-xs font-semibold text-gray-700 mb-2 uppercase tracking-wide cursor-pointer hover:text-gray-900 flex items-center gap-2">
                              <svg className="w-4 h-4 text-gray-400 group-open:rotate-90 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                              </svg>
                              Python Code (click to expand)
                            </summary>
                            <div className="bg-gray-900 rounded-lg overflow-hidden mt-2">
                              <pre className="p-4 text-sm text-gray-100 overflow-x-auto max-h-96 overflow-y-auto">
                                <code>{detail.code}</code>
                              </pre>
                            </div>
                          </details>
                        ) : (
                          <>
                            <p className="text-xs font-semibold text-gray-700 mb-2 uppercase tracking-wide">Python Code</p>
                            <div className="bg-gray-900 rounded-lg overflow-hidden">
                              <pre className="p-4 text-sm text-gray-100 overflow-x-auto max-h-96 overflow-y-auto">
                                <code>{detail.code}</code>
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

        {/* VERBOSE MODE SECTIONS */}

        {/* Methodology & Data Sources */}
        {report.methodology && (
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <span className="w-1 h-6 bg-cyan-600 rounded"></span>
              Methodology & Data Sources
            </h2>
            <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-6">
              {/* Overview Stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-2xl font-bold text-gray-900">
                    {report.methodology.total_sub_questions}
                  </div>
                  <div className="text-xs text-gray-600 mt-1">Sub-Questions</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-2xl font-bold text-gray-900">
                    {report.methodology.data_sources?.total_rows?.toLocaleString()}
                  </div>
                  <div className="text-xs text-gray-600 mt-1">Data Rows</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-2xl font-bold text-gray-900">
                    {report.methodology.data_sources?.dataset_columns}
                  </div>
                  <div className="text-xs text-gray-600 mt-1">Columns Analyzed</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-2xl font-bold text-cyan-600">
                    {report.methodology.quality_metrics?.coverage_percentage}%
                  </div>
                  <div className="text-xs text-gray-600 mt-1">Success Rate</div>
                </div>
              </div>

              {/* Analysis Methods */}
              {report.methodology.analysis_methods && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-2">Analysis Methods</h3>
                  <div className="flex flex-wrap gap-2">
                    {report.methodology.analysis_methods.map((method: string, idx: number) => (
                      <span key={idx} className="px-3 py-1 bg-cyan-100 text-cyan-700 rounded-full text-sm">
                        {method}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </section>
        )}

        {/* Detailed Findings */}
        {report.detailed_findings && report.detailed_findings.length > 0 && (
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <span className="w-1 h-6 bg-emerald-600 rounded"></span>
              Detailed Findings
            </h2>
            <div className="space-y-6">
              {report.detailed_findings.map((finding: any, idx: number) => (
                <div key={idx} className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                  <div className="bg-emerald-50 px-6 py-4 border-b border-gray-200">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm font-semibold text-emerald-700">Finding {idx + 1}</span>
                          {finding.confidence && (
                            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                              finding.confidence === 'high' ? 'bg-green-100 text-green-700' :
                              finding.confidence === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                              'bg-gray-100 text-gray-700'
                            }`}>
                              {finding.confidence} confidence
                            </span>
                          )}
                        </div>
                        <h3 className="text-lg font-semibold text-gray-900">{finding.finding_title}</h3>
                        <p className="text-sm text-gray-600 mt-1">{finding.question}</p>
                      </div>
                    </div>
                  </div>
                  <div className="px-6 py-5 space-y-4">
                    {/* Analysis */}
                    <div>
                      <h4 className="text-sm font-semibold text-gray-700 mb-2">Analysis</h4>
                      <p className="text-gray-700 leading-relaxed">{finding.analysis}</p>
                    </div>

                    {/* Data Points */}
                    {finding.data_points && finding.data_points.length > 0 && (
                      <div>
                        <h4 className="text-sm font-semibold text-gray-700 mb-2">Key Data Points</h4>
                        <ul className="space-y-1">
                          {finding.data_points.map((point: string, pidx: number) => (
                            <li key={pidx} className="flex items-start gap-2">
                              <span className="text-emerald-600 font-bold">•</span>
                              <span className="text-gray-700">{point}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Implications */}
                    {finding.implications && (
                      <div>
                        <h4 className="text-sm font-semibold text-gray-700 mb-2">Implications</h4>
                        <p className="text-gray-700 bg-emerald-50 border-l-4 border-emerald-400 p-3 rounded-r">
                          {finding.implications}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Cross-Analysis & Patterns */}
        {report.cross_analysis && (
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <span className="w-1 h-6 bg-orange-600 rounded"></span>
              Cross-Analysis & Patterns
            </h2>
            <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-6">
              {/* Patterns */}
              {report.cross_analysis.patterns && report.cross_analysis.patterns.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-3">🔍 Patterns Identified</h3>
                  <div className="space-y-2">
                    {report.cross_analysis.patterns.map((pattern: string, idx: number) => (
                      <div key={idx} className="flex items-start gap-2 bg-orange-50 p-3 rounded">
                        <span className="text-orange-600 font-bold">{idx + 1}.</span>
                        <span className="text-gray-700">{pattern}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Correlations */}
              {report.cross_analysis.correlations && report.cross_analysis.correlations.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-3">📈 Correlations</h3>
                  <div className="space-y-2">
                    {report.cross_analysis.correlations.map((corr: string, idx: number) => (
                      <div key={idx} className="flex items-start gap-2 bg-blue-50 p-3 rounded">
                        <span className="text-blue-600 font-bold">↔</span>
                        <span className="text-gray-700">{corr}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Anomalies */}
              {report.cross_analysis.anomalies && report.cross_analysis.anomalies.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-3">⚡ Anomalies</h3>
                  <div className="space-y-2">
                    {report.cross_analysis.anomalies.map((anomaly: string, idx: number) => (
                      <div key={idx} className="flex items-start gap-2 bg-red-50 p-3 rounded border-l-2 border-red-400">
                        <span className="text-red-600 font-bold">!</span>
                        <span className="text-gray-700">{anomaly}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Trends */}
              {report.cross_analysis.trends && report.cross_analysis.trends.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-3">📊 Trends</h3>
                  <div className="space-y-2">
                    {report.cross_analysis.trends.map((trend: string, idx: number) => (
                      <div key={idx} className="flex items-start gap-2 bg-green-50 p-3 rounded">
                        <span className="text-green-600 font-bold">→</span>
                        <span className="text-gray-700">{trend}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </section>
        )}

        {/* Limitations & Caveats */}
        {report.limitations && report.limitations.length > 0 && (
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <span className="w-1 h-6 bg-amber-600 rounded"></span>
              Limitations & Caveats
            </h2>
            <div className="bg-amber-50 border-l-4 border-amber-500 p-6 rounded-r-lg">
              <div className="flex items-start gap-3 mb-4">
                <svg className="w-6 h-6 text-amber-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <div className="flex-1">
                  <h3 className="text-sm font-semibold text-amber-900 mb-1">Important Limitations</h3>
                  <p className="text-sm text-amber-700">
                    Please consider these constraints when interpreting the analysis:
                  </p>
                </div>
              </div>
              <ul className="space-y-3">
                {report.limitations.map((limitation: any, idx: number) => {
                  // Handle both string and object formats
                  const text = typeof limitation === 'string'
                    ? limitation
                    : limitation.description || limitation.type || JSON.stringify(limitation)
                  const title = typeof limitation === 'object' && limitation.type
                    ? limitation.type
                    : null

                  return (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-amber-600 font-bold flex-shrink-0">{idx + 1}.</span>
                      <div className="text-amber-900">
                        {title && <strong className="font-semibold block mb-1">{title}:</strong>}
                        <span>{text}</span>
                      </div>
                    </li>
                  )
                })}
              </ul>
            </div>
          </section>
        )}

        {/* Recommendations & Next Steps */}
        {report.recommendations && report.recommendations.length > 0 && (
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <span className="w-1 h-6 bg-violet-600 rounded"></span>
              Recommendations & Next Steps
            </h2>
            <div className="space-y-4">
              {report.recommendations.map((rec: any, idx: number) => (
                <div key={idx} className="bg-white border-2 border-violet-200 rounded-lg overflow-hidden">
                  <div className={`px-5 py-3 ${
                    rec.priority === 'high' ? 'bg-red-50 border-b-2 border-red-200' :
                    rec.priority === 'medium' ? 'bg-yellow-50 border-b-2 border-yellow-200' :
                    'bg-gray-50 border-b-2 border-gray-200'
                  }`}>
                    <div className="flex items-center gap-2">
                      <span className={`text-xs px-2 py-1 rounded-full font-semibold uppercase ${
                        rec.priority === 'high' ? 'bg-red-200 text-red-800' :
                        rec.priority === 'medium' ? 'bg-yellow-200 text-yellow-800' :
                        'bg-gray-200 text-gray-800'
                      }`}>
                        {rec.priority} Priority
                      </span>
                      <span className="text-sm font-semibold text-gray-700">Recommendation {idx + 1}</span>
                    </div>
                  </div>
                  <div className="px-5 py-4 space-y-3">
                    <div>
                      <h4 className="text-sm font-semibold text-gray-700 mb-1">Action</h4>
                      <p className="text-gray-900 font-medium">{rec.recommendation}</p>
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold text-gray-700 mb-1">Rationale</h4>
                      <p className="text-gray-700">{rec.rationale}</p>
                    </div>
                    {rec.requirements && (
                      <div>
                        <h4 className="text-sm font-semibold text-gray-700 mb-1">Requirements</h4>
                        <p className="text-gray-600 text-sm bg-gray-50 p-3 rounded">{rec.requirements}</p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Technical Appendix */}
        {report.technical_appendix && (
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <span className="w-1 h-6 bg-slate-600 rounded"></span>
              Technical Appendix
            </h2>
            <details className="bg-white border border-gray-200 rounded-lg">
              <summary className="px-6 py-4 cursor-pointer hover:bg-gray-50 font-medium text-gray-700 flex items-center justify-between">
                <span>📋 View Technical Details</span>
                <svg className="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </summary>
              <div className="px-6 py-5 border-t border-gray-200 space-y-6">
                {/* Classification Breakdown */}
                {report.technical_appendix.classification_breakdown && (
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-3">Query Classification</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      <div className="bg-blue-50 rounded p-3">
                        <div className="text-xl font-bold text-blue-700">
                          {report.technical_appendix.classification_breakdown.data_backed || 0}
                        </div>
                        <div className="text-xs text-blue-600">Data-Backed</div>
                      </div>
                      <div className="bg-purple-50 rounded p-3">
                        <div className="text-xl font-bold text-purple-700">
                          {report.technical_appendix.classification_breakdown.world_knowledge || 0}
                        </div>
                        <div className="text-xs text-purple-600">World Knowledge</div>
                      </div>
                      <div className="bg-green-50 rounded p-3">
                        <div className="text-xl font-bold text-green-700">
                          {report.technical_appendix.classification_breakdown.mixed || 0}
                        </div>
                        <div className="text-xs text-green-600">Mixed</div>
                      </div>
                      <div className="bg-gray-50 rounded p-3">
                        <div className="text-xl font-bold text-gray-700">
                          {report.technical_appendix.classification_breakdown.insufficient_data || 0}
                        </div>
                        <div className="text-xs text-gray-600">Insufficient Data</div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Schema Summary */}
                {report.technical_appendix.schema_summary && (
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-3">Dataset Schema</h3>
                    <div className="text-sm text-gray-600 mb-2">
                      {report.technical_appendix.schema_summary.total_columns} columns, {report.technical_appendix.schema_summary.total_rows?.toLocaleString()} rows
                    </div>
                    {report.technical_appendix.schema_summary.columns && report.technical_appendix.schema_summary.columns.length > 0 && (
                      <div className="bg-gray-50 rounded p-3 max-h-60 overflow-y-auto">
                        <table className="w-full text-xs">
                          <thead>
                            <tr className="text-left border-b border-gray-200">
                              <th className="pb-2 font-semibold">Column</th>
                              <th className="pb-2 font-semibold">Type</th>
                            </tr>
                          </thead>
                          <tbody>
                            {report.technical_appendix.schema_summary.columns.map((col: any, idx: number) => (
                              <tr key={idx} className="border-b border-gray-100">
                                <td className="py-2 font-mono">{col.name}</td>
                                <td className="py-2 text-gray-600">{col.type}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                )}

                {/* Queries Executed */}
                {report.technical_appendix.queries_executed && report.technical_appendix.queries_executed.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-3">
                      Queries Executed ({report.technical_appendix.queries_executed.length})
                    </h3>
                    <div className="space-y-2 max-h-80 overflow-y-auto">
                      {report.technical_appendix.queries_executed.map((query: any, idx: number) => (
                        <details key={idx} className="bg-gray-50 border border-gray-200 rounded">
                          <summary className="p-3 cursor-pointer hover:bg-gray-100 transition">
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-gray-700">{idx + 1}.</span>
                              <span className={`px-2 py-0.5 rounded-full font-medium text-xs ${
                                query.method === 'sql' ? 'bg-blue-100 text-blue-700' :
                                query.method === 'python' ? 'bg-purple-100 text-purple-700' :
                                'bg-gray-100 text-gray-700'
                              }`}>
                                {query.method.toUpperCase()}
                              </span>
                              <span className={`px-2 py-0.5 rounded-full font-medium text-xs ${
                                query.success ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                              }`}>
                                {query.success ? '✓ Success' : '✗ Failed'}
                              </span>
                              {query.execution_time_ms && (
                                <span className="text-gray-500 text-xs">{query.execution_time_ms}ms</span>
                              )}
                              <span className="text-gray-700 text-sm flex-1 truncate ml-2">{query.question}</span>
                            </div>
                          </summary>
                          <div className="px-3 pb-3 pt-2 border-t border-gray-200 bg-white">
                            <div className="text-xs font-semibold text-gray-600 mb-2">
                              {query.method === 'sql' ? 'SQL Query:' : 'Python Code:'}
                            </div>
                            {query.code ? (
                              <pre className="bg-gray-900 text-gray-100 p-3 rounded text-xs overflow-x-auto max-h-64 overflow-y-auto">
                                <code>{query.code}</code>
                              </pre>
                            ) : (
                              <div className="text-gray-500 text-xs italic">No code available</div>
                            )}
                            {!query.success && query.error && (
                              <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs">
                                <div className="font-semibold text-red-700 mb-1">Error:</div>
                                <div className="text-red-600">{query.error}</div>
                              </div>
                            )}
                          </div>
                        </details>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </details>
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
