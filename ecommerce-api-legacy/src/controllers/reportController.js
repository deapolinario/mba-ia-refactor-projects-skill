const reportModel = require('../models/report');

async function getFinancialReport() {
    return reportModel.financialReport();
}

module.exports = { getFinancialReport };
