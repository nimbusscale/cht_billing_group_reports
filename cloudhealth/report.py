class CostHistory:

    def __init__(self, client, perspective_id, group_id):
        self._client = client
        self._client.add_param({'dimensions[]':
                                    ['AWS-Account', 'AWS-Service-Category']})
        self._client.add_param({'measures[]': 'cost'})
        group_filter = 'Groupset-{}:select:{}'.format(perspective_id,
                                                      group_id)
        self._client.add_param({'filters[]':
                                [group_filter,
                                 'time:select:-2']})
        self._uri = 'olap_reports/cost/history'

    @property
    def raw_json(self):
        response = self._client.get(self._uri)
        return response

    def _validate_total(self, cost_lists):
        """cost_lists is a list of lists, where each list is the costs for a
        specific AWS services. The first list in cost_list is assumed to be the
        totals. _validate_total adds up all the related items in the lists and
        compares them to the expected total.

        This is used to make sure no unexpected subtotal items have been
        included by CloudHealth.

        Returns True if calculated totals match report total, otherwise False
        """
        # calculated_totals contains a list of totals for each account
        # (i.e. column in cost_lists). This line initalizes the list at 0 for
        # each account
        calculated_totals = [0 for _ in cost_lists[0]]
        for cost_item in cost_lists[1:-1]:
            for column, cost in enumerate(cost_item):
                calculated_totals[column] = calculated_totals[column] + cost
        for column, calculated_total in enumerate(calculated_totals):
            report_total = cost_lists[0][column]
            rounded_calculated_total = round(calculated_total, 4)
            rounded_report_total = round(report_total, 4)
            if rounded_calculated_total != rounded_report_total:
                return False
        return True

    @property
    def output(self):
        json = self.raw_json

        raw_columns = None
        raw_rows = None
        for dimension in json['dimensions']:
            if 'AWS-Account' in dimension.keys():
                raw_columns = [account['label'] for account in
                               dimension['AWS-Account']]
            elif 'AWS-Service-Category' in dimension.keys():
                raw_rows = [account['label'] for account in
                            dimension['AWS-Service-Category']]
        if raw_columns is None or raw_rows is None:
            exception_message = (
                "report does not include AWS-Account or AWS-Service-Category "
                "as dimensions"
            )
            raise ValueError(exception_message)
        raw_data = json['data']

        # stores a list of account names
        accounts = []
        # stores lists of costs for each account. Index for each list
        # corrisponds to index of account in accounts list.
        accounts_cost_lists = []

        # CH API response can include accounts that are not part of the
        # perspective. If the data returned for account is not all None's
        # then we add it's name and costs to the appropriate lists.
        # This filters out accounts with costs that are all None's
        for column_number, column in enumerate(raw_columns):
            # raw_data includes a list of lists containing a single item
            # Therefore we need to compare vs the contents of the lists with
            # cost[0]
            if not all(cost[0] is None for cost in raw_data[column_number]):
                accounts.append(column)
                accounts_cost_lists.append(raw_data[column_number])

        # CH API response includes subtotal items along with individual cost
        # items. There is no way to identify a subtotal item vs a standard
        # charge via the API and these items can be confusing on a report if
        # they are included.
        subtotal_items = [
                          "Amazon DynamoDB",
                          "Amazon DynamoDB - Direct",
                          "Amazon Elastic Compute Cloud",
                          "Amazon Elastic Compute Cloud - Direct",
                          "Amazon RDS Service - Direct",
                          "Amazon S3 - Direct"
                          ]
        accounts_csv = "Headers," + ",".join(map(str, accounts))
        report_csv = accounts_csv + "\n"
        # service_cost_lists store lists of costs on a service by service basis
        # vs account by account basis as found in accounts_cost_lists
        service_cost_lists = []
        for service_number, service in enumerate(raw_rows):
            # exclude service if they are a subtotal_item
            if service not in subtotal_items:
                # take the corrisoponding cost data for each service from the
                # accounts_cost_lists
                service_cost_list = []
                for column_number, column in enumerate(accounts):
                    service_cost_list.append(
                        accounts_cost_lists[column_number][service_number][0]
                    )
                # exclude any service with all 0 Cost or None data
                # None data is provided when an account does use the service
                # Some accounts may use a service, while others might not, so
                # there could None's mixed in. But we want to ignore anything
                # that is all None's
                if not all(cost is None or cost == 0
                           for cost in service_cost_list):
                    # Replace None's with 0s
                    service_cost_list = [cost if cost is not None else 0
                                         for cost in service_cost_list]
                    service_cost_lists.append(service_cost_list)
                    cost_csv = ",".join(map(str,service_cost_list))
                    report_csv = report_csv + "{}, {}\n".format(service,
                                                                cost_csv)
        print(service_cost_lists[-1])
        if not self._validate_total(service_cost_lists):
            report_csv = (
                "TOTALS DESCREPENCY DETECTED - "
                "report total does not match totals of all items. "
                "This occurs when a subtotal item has not be excluded from "
                "the report.\n" + report_csv
            )
        return report_csv
