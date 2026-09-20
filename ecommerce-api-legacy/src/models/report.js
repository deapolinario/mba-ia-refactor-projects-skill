const { getDb, dbAll } = require('../database');

/**
 * v2.2 - substitui o financial-report original, que fazia 1 query de
 * enrollments por course + 2 queries (user, payment) por enrollment em
 * callbacks aninhados (N+1 / callback hell). Agora é 1 única query com
 * JOINs, agrupada em memória.
 */
async function financialReport() {
    const rows = await dbAll(
        getDb(),
        `SELECT
            c.id AS course_id,
            c.title AS course_title,
            u.name AS student_name,
            p.amount AS paid_amount,
            p.status AS payment_status
        FROM courses c
        LEFT JOIN enrollments e ON e.course_id = c.id
        LEFT JOIN users u ON u.id = e.user_id
        LEFT JOIN payments p ON p.enrollment_id = e.id
        ORDER BY c.id`
    );

    const byCourseId = new Map();
    const order = [];

    for (const row of rows) {
        if (!byCourseId.has(row.course_id)) {
            byCourseId.set(row.course_id, { course: row.course_title, revenue: 0, students: [] });
            order.push(row.course_id);
        }
        const courseData = byCourseId.get(row.course_id);
        if (row.student_name !== null) {
            if (row.payment_status === 'PAID') {
                courseData.revenue += row.paid_amount;
            }
            courseData.students.push({
                student: row.student_name || 'Unknown',
                paid: row.paid_amount || 0
            });
        }
    }

    return order.map((id) => byCourseId.get(id));
}

module.exports = { financialReport };
