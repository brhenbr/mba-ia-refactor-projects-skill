class ReportService {
    constructor(reportRepository) {
        this.reportRepository = reportRepository;
    }

    getFinancialReport() {
        return this.reportRepository.getFinancialReport();
    }
}

module.exports = { ReportService };
