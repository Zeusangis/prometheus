import type { NewJobInput } from "../api/jobs";

export function consoleData(title: string, data: unknown) {
  const timestamp = new Date().toISOString();

  console.group(`[${title}] ${timestamp}`);
  console.log("Raw data:", data);

  try {
    console.log("Pretty JSON:", JSON.stringify(data, null, 2));
  } catch {
    console.log("Pretty JSON:", "Unable to serialize data");
  }

  console.groupEnd();
}

export function consoleNewJobFormData(data: NewJobInput) {
  const timestamp = new Date().toISOString();

  console.group(`[Create Job Form Data] ${timestamp}`);

  console.group("Job details");
  console.log("title:", data.title);
  console.log("jobType:", data.jobType);
  console.log("description:", data.description);
  console.log("languages:", data.languages);
  console.log("frameworks:", data.frameworks);
  console.groupEnd();

  console.group("GitHub scraper");
  Object.entries(data.scraperMetrics).forEach(([metricKey, metric]) => {
    console.log(`${metricKey}.enabled:`, metric.enabled);
    console.log(`${metricKey}.weight:`, metric.weight);
  });
  console.log("scraperInstructions:", data.scraperInstructions);
  console.groupEnd();

  console.group("AI interview");
  console.log("interviewTone:", data.interviewTone);
  console.log("interviewFocus:", data.interviewFocus);
  console.log("customQuestions:", data.customQuestions);
  console.log("interviewLength:", data.interviewLength);
  console.log("interviewInstructions:", data.interviewInstructions);
  console.groupEnd();

  console.group("Raw payload");
  console.log(data);
  console.groupEnd();

  console.groupEnd();
}
