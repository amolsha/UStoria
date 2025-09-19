fetch("/dashboard/data")
  .then(response => response.json())
  .then(data => {
    const ctx = document.getElementById('criteriaChart').getContext('2d');
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels: data.criteria,
        datasets: [
          {
            label: 'Passed',
            data: data.passed,
            backgroundColor: 'rgba(75, 192, 192, 0.7)'
          },
          {
            label: 'Failed',
            data: data.failed,
            backgroundColor: 'rgba(255, 99, 132, 0.7)'
          }
        ]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'top' },
          title: { display: true, text: 'Evaluation Results per Criterion' }
        }
      }
    });
  });
